# project/generation/video_builder.py
import logging
import random
import subprocess
from pathlib import Path
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [VideoBuilder] - %(message)s')

def _get_random_asset(asset_dir: Path) -> Path | None:
    if not asset_dir.exists() or not any(asset_dir.iterdir()): return None
    return random.choice(list(asset_dir.iterdir()))

def run_ffmpeg_command(command: list, step_name: str, timeout: int = 180) -> bool:
    """A helper function to run an FFmpeg command and log its output."""
    logging.info(f"Executing FFmpeg Step: {step_name}...")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate(timeout=timeout)
        if process.returncode != 0:
            logging.error(f"--- FFmpeg Step '{step_name}' FAILED! ---")
            logging.error(f"Command: {' '.join(map(str, command))}")
            logging.error(f"FFmpeg stderr:\n{stderr}")
            return False
        logging.info(f"FFmpeg Step '{step_name}' successful.")
        return True
    except subprocess.TimeoutExpired:
        logging.error(f"--- FFmpeg Step '{step_name}' timed out after {timeout} seconds. ---")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during FFmpeg step '{step_name}': {e}")
        return False

def build_video(audio_path: Path, subtitles_path: Path, unique_id: str) -> Path | None:
    logging.info(f"--- Starting 2-STEP Video Build for ID: {unique_id} ---")
    
    background_video_path = _get_random_asset(config.BACKGROUND_VIDEOS_DIR)
    background_music_path = _get_random_asset(config.BACKGROUND_MUSIC_DIR)
    if not all([background_video_path, background_music_path]): return None

    # --- Define file paths ---
    subtitled_video_path = config.TEMP_VIDEOS_DIR / f"subtitled_{unique_id}.mp4"
    final_video_path = config.TEMP_VIDEOS_DIR / f"final_video_{unique_id}.mp4"
    subtitled_video_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Corrected force_style syntax with commas instead of colons
    subtitle_style = f"Fontfile='{config.CAPTION_FONT_FILE}', Fontsize={config.CAPTION_FONT_SIZE}, PrimaryColour=&H00FFFFFF, BorderStyle=1, Outline=2, Shadow=1, Alignment=2, MarginV={int(config.VIDEO_HEIGHT * 0.15)}"

    # --- STEP 1: Burn subtitles onto the background video ---
    command1 = [
        "ffmpeg", "-y",
        "-i", str(background_video_path),
        "-vf", (
            f"crop=ih*9/16:ih,scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},setsar=1,"
            f"subtitles={subtitles_path}:force_style='{subtitle_style}'"
        ),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
        "-an", # No audio in this intermediate file
        str(subtitled_video_path)
    ]
    if not run_ffmpeg_command(command1, "Burn Subtitles"):
        return None

    # --- STEP 2: Add voiceover and music to the subtitled video ---
    command2 = [
        "ffmpeg", "-y",
        "-i", str(subtitled_video_path),
        "-i", str(audio_path),
        "-i", str(background_music_path),
        "-filter_complex", "[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[voice];" +
                         "[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=" + str(config.MUSIC_VOLUME) + "[music];" +
                         "[voice][music]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "0:v:0",
        "-map", "[a]",
        "-c:v", "copy", # Just copy the video stream, don't re-encode
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(final_video_path)
    ]
    if not run_ffmpeg_command(command2, "Add Audio"):
        return None

    logging.info(f"Final video successfully created at: {final_video_path}")
    # Optional: Clean up the intermediate subtitled file
    if subtitled_video_path.exists():
        subtitled_video_path.unlink()
    return final_video_path
