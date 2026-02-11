# project/generation/video_builder.py

import logging
import random
import subprocess
from pathlib import Path

# Import project-specific modules
import config

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [VideoBuilder] - %(message)s')


def _get_random_asset(asset_dir: Path) -> Path | None:
    """Selects a random file from a given asset directory."""
    if not asset_dir.exists() or not any(asset_dir.iterdir()):
        logging.error(f"Asset directory is empty or does not exist: {asset_dir}")
        return None
    assets = list(asset_dir.iterdir())
    return random.choice(assets)


def _escape_path_for_ffmpeg(path: Path) -> str:
    """Prepares a path for use in an FFmpeg filter string, especially for Windows."""
    # Use forward slashes and escape colons (for Windows drive letters)
    return path.as_posix().replace(':', '\\:')


def build_video(audio_path: Path, subtitles_path: Path, unique_id: str) -> Path | None:
    """
    Builds the final video by merging background video, music, voiceover, and captions.

    Args:
        audio_path: Path to the generated voiceover audio file (.wav).
        subtitles_path: Path to the generated subtitle file (.srt).
        unique_id: A unique identifier for the output filename.

    Returns:
        A Path object to the final rendered video file on success, otherwise None.
    """
    logging.info(f"--- Starting Video Build Process for ID: {unique_id} ---")

    # 1. Select Background Assets
    background_video_path = _get_random_asset(config.BACKGROUND_VIDEOS_DIR)
    background_music_path = _get_random_asset(config.BACKGROUND_MUSIC_DIR)

    if not all([background_video_path, background_music_path, audio_path.exists(), subtitles_path.exists()]):
        logging.error("Missing one or more required asset files. Aborting video build.")
        return None

    logging.info(f"Selected video: {background_video_path.name}")
    logging.info(f"Selected music: {background_music_path.name}")

    # 2. Define Output Path
    output_filename = f"final_video_{unique_id}.mp4"
    output_path = config.TEMP_VIDEOS_DIR / output_filename
    config.TEMP_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    # 3. Prepare FFmpeg filter components
    escaped_subtitles_path = _escape_path_for_ffmpeg(subtitles_path)

    # Extract font name from file path, assuming it's like 'Arial-Bold.ttf' -> 'Arial-Bold'
    font_name = Path(config.CAPTION_FONT_FILE).stem

    # Alignment=2 is Bottom-Center for SSA/ASS style used by the filter
    # MarginV is the vertical margin from the bottom of the video
    vertical_margin = int(config.VIDEO_HEIGHT * 0.15)

    subtitle_style = (
        f"FontName={font_name},"
        f"FontSize={config.CAPTION_FONT_SIZE},"
        "PrimaryColour=&H00FFFFFF,"  # Opaque White
        "BorderStyle=1,"  # Outline + Shadow
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"  # Bottom Center
        f"MarginV={vertical_margin}"
    )

    # 4. Construct the FFmpeg Command
    # This complex command performs all operations in one go for efficiency.
    command = [
        "ffmpeg",
        "-y",  # Overwrite output file if it exists

        # --- Inputs ---
        "-stream_loop", "-1", "-i", str(background_video_path),  # Input 0: Loop background video
        "-i", str(audio_path),  # Input 1: Voiceover audio
        "-stream_loop", "-1", "-i", str(background_music_path),  # Input 2: Loop background music

        # --- Filter Complex ---
        # This is where all the magic happens
        "-filter_complex", (
            # 1. Process video: crop to 9:16, scale, and burn subtitles
            f"[0:v]crop=ih*9/16:ih,scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},setsar=1[v_scaled];"
            f"[v_scaled]subtitles='{escaped_subtitles_path}':force_style='{subtitle_style}'[v];"

            # 2. Process audio: lower music volume and mix with voiceover
            f"[2:a]volume={config.MUSIC_VOLUME}[bgm];"
            "[1:a][bgm]amix=inputs=2:duration=first[a]"
        ),

        # --- Mapping and Encoding ---
        "-map", "[v]",  # Map the final video stream
        "-map", "[a]",  # Map the final audio stream
        "-c:v", "libx264",  # Video codec
        "-preset", "veryfast",  # Good speed/quality balance for automation
        "-crf", "23",  # Constant Rate Factor for quality
        "-c:a", "aac",  # Audio codec
        "-b:a", "192k",  # Audio bitrate
        "-shortest",  # Finish encoding when the shortest stream ends (the voiceover)
        str(output_path)
    ]

    # 5. Execute the Command
    logging.info("Executing FFmpeg command...")
    try:
        # We use Popen and communicate to handle long processes and get detailed logs
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            logging.error("--- FFmpeg command failed! ---")
            logging.error(f"Return Code: {process.returncode}")
            logging.error("\n--- FFmpeg Standard Error ---\n" + stderr)
            return None

        logging.info("FFmpeg command executed successfully.")
        logging.info(f"Final video saved to: {output_path}")
        return output_path

    except FileNotFoundError:
        logging.error("FFmpeg not found. Please ensure it is installed and in your system's PATH.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while running FFmpeg: {e}")
        return None


# --- Standalone Test Block ---
if __name__ == '__main__':
    from generation.tts import generate_tts_audio
    from generation.captions import generate_captions

    print("Running video_builder.py in standalone mode for testing...")
    print("NOTE: This test requires at least one video in 'assets/videos' and one audio file in 'assets/music'.")

    # Create dummy assets and directories if they don't exist
    for directory in config.REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)

    # Check for required background assets
    if not any(config.BACKGROUND_VIDEOS_DIR.iterdir()) or not any(config.BACKGROUND_MUSIC_DIR.iterdir()):
        print("\n❌ --- MISSING ASSETS --- ❌")
        print("Please add at least one .mp4 file to 'project/assets/videos/'")
        print("And at least one .mp3 or .wav file to 'project/assets/music/' before running this test.")
    else:
        # Generate dummy audio and srt for the test
        test_script = "This is a full pipeline test of the video builder. If you see this text burned into the video with a voiceover and background music, the system is working."
        test_id = "standalone_video_test_001"

        audio_path = generate_tts_audio(test_script, test_id)
        if audio_path:
            captions_path = generate_captions(audio_path, test_id)
            if captions_path:
                # Now, build the video
                video_path = build_video(audio_path, captions_path, test_id)
                if video_path and video_path.exists():
                    print("\n✅ --- VIDEO BUILT SUCCESSFULLY --- ✅")
                    print(f"File saved at: {video_path}")
                    print(
                        "Please watch the video to verify all components (video, music, voice, captions) are correct.")
                else:
                    print("\n❌ --- VIDEO BUILD FAILED --- ❌")
            else:
                print("\n❌ --- FAILED TO GENERATE TEST CAPTIONS --- ❌")
        else:
            print("\n❌ --- FAILED TO GENERATE TEST AUDIO --- ❌")