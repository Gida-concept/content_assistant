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

def build_video(audio_path: Path, subtitles_path: Path, unique_id: str) -> Path | None:
    logging.info(f"--- Starting Final Video Build for ID: {unique_id} ---")
    
    background_video_path = _get_random_asset(config.BACKGROUND_VIDEOS_DIR)
    background_music_path = _get_random_asset(config.BACKGROUND_MUSIC_DIR)
    
    if not all([background_video_path, background_music_path, audio_path.exists(), subtitles_path.exists()]):
        logging.error("Missing assets.")
        return None

    final_video_path = config.TEMP_VIDEOS_DIR / f"final_video_{unique_id}.mp4"
    final_video_path.parent.mkdir(parents=True, exist_ok=True)
    
    subtitle_style = f"Fontfile='{config.CAPTION_FONT_FILE}', Fontsize={config.CAPTION_FONT_SIZE}, PrimaryColour=&H00FFFFFF, BorderStyle=1, Outline=2, Shadow=1, Alignment=2, MarginV={int(config.VIDEO_HEIGHT * 0.15)}"

    command = [
        "ffmpeg", "-y",
        "-i", str(background_video_path),
        "-i", str(audio_path),
        "-i", str(background_music_path),
        "-filter_complex", (
            f"[0:v]crop=ih*9/16:ih,scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},setsar=1,"
            f"subtitles={subtitles_path}:force_style='{subtitle_style}'[v];"
            f"[1:a]aformat=channel_layouts=stereo,volume={config.VOICE_VOLUME}[voice];"
            f"[2:a]aformat=channel_layouts=stereo,volume={config.MUSIC_VOLUME}[music];"
            "[voice][music]amix=inputs=2:duration=first:dropout_transition=0[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-shortest",
        str(final_video_path)
    ]

    logging.info("Executing final FFmpeg command...")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate(timeout=180)

        if process.returncode != 0:
            logging.error(f"--- Final FFmpeg command FAILED! ---\n{stderr}")
            return None
        
        logging.info(f"Final video successfully created at: {final_video_path}")
        return final_video_path
    except subprocess.TimeoutExpired:
        logging.error("--- Final FFmpeg command timed out. ---")
        return None
    except Exception as e:
        logging.error(f"Error: {e}")
        return None
