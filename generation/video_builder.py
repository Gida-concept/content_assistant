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

def build_video(audio_path: Path, subtitles_path: Path, unique_id: str) -> Path | None:
    """
    Builds the final video by merging background video, music, voiceover, and captions.
    """
    logging.info(f"--- Starting Video Build Process for ID: {unique_id} ---")

    background_video_path = _get_random_asset(config.BACKGROUND_VIDEOS_DIR)
    background_music_path = _get_random_asset(config.BACKGROUND_MUSIC_DIR)

    if not all([background_video_path, background_music_path, audio_path.exists(), subtitles_path.exists()]):
        logging.error("Missing one or more required asset files. Aborting video build.")
        return None

    logging.info(f"Selected video: {background_video_path.name}")
    logging.info(f"Selected music: {background_music_path.name}")

    output_filename = f"final_video_{unique_id}.mp4"
    output_path = config.TEMP_VIDEOS_DIR / output_filename
    config.TEMP_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    font_name = Path(config.CAPTION_FONT_FILE).stem
    vertical_margin = int(config.VIDEO_HEIGHT * 0.15)
    
    subtitle_style = (
        f"FontName={font_name},"
        f"FontSize={config.CAPTION_FONT_SIZE},"
        "PrimaryColour=&H00FFFFFF,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        f"MarginV={vertical_margin}"
    )

    # Simplified command for better Linux compatibility
    command = [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1", "-i", str(background_video_path),
        "-i", str(audio_path),
        "-stream_loop", "-1", "-i", str(background_music_path),
        "-filter_complex", (
            f"[0:v]crop=ih*9/16:ih,scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},setsar=1[v_scaled];"
            # The corrected, simpler subtitles part
            f"[v_scaled]subtitles={subtitles_path}:force_style='{subtitle_style}'[v];"
            f"[2:a]volume={config.MUSIC_VOLUME}[bgm];"
            "[1:a][bgm]amix=inputs=2:duration=first[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path)
    ]

    logging.info("Executing FFmpeg command...")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate(timeout=300) # Add a 5-minute timeout

        if process.returncode != 0:
            logging.error("--- FFmpeg command failed! ---")
            logging.error(f"Return Code: {process.returncode}")
            logging.error("\n--- FFmpeg Standard Error ---\n" + stderr)
            return None
        
        logging.info("FFmpeg command executed successfully.")
        logging.info(f"Final video saved to: {output_path}")
        return output_path

    except subprocess.TimeoutExpired:
        logging.error("--- FFmpeg command timed out after 5 minutes. ---")
        process.kill()
        return None
    except FileNotFoundError:
        logging.error("FFmpeg not found. Please ensure it is installed and in your system's PATH.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while running FFmpeg: {e}")
        return None

# --- Standalone Test Block --- (omitted for brevity, no change needed)
