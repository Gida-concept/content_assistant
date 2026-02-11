# project/generation/video_builder.py

import logging
import random
import subprocess
from pathlib import Path
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [VideoBuilder] - %(message)s')

def _get_random_asset(asset_dir: Path) -> Path | None:
    # ... (no changes needed in this helper function)
    if not asset_dir.exists() or not any(asset_dir.iterdir()):
        logging.error(f"Asset directory is empty or does not exist: {asset_dir}")
        return None
    assets = list(asset_dir.iterdir())
    return random.choice(assets)

def build_video(audio_path: Path, subtitles_path: Path, unique_id: str) -> Path | None:
    logging.info(f"--- Starting Video Build Process for ID: {unique_id} ---")
    
    background_video_path = _get_random_asset(config.BACKGROUND_VIDEOS_DIR)
    background_music_path = _get_random_asset(config.BACKGROUND_MUSIC_DIR)

    if not all([background_video_path, background_music_path, audio_path.exists(), subtitles_path.exists()]):
        logging.error("Missing one or more required asset files. Aborting video build.")
        return None

    output_filename = f"final_video_{unique_id}.mp4"
    output_path = config.TEMP_VIDEOS_DIR / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    font_name = Path(config.CAPTION_FONT_FILE).stem
    vertical_margin = int(config.VIDEO_HEIGHT * 0.15)
    
    subtitle_style = f"FontName={font_name},FontSize={config.CAPTION_FONT_SIZE},PrimaryColour=&H00FFFFFF,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV={vertical_margin}"

    command = [
        "ffmpeg", "-y",
        "-i", str(background_video_path),
        "-i", str(audio_path),
        "-i", str(background_music_path),
        "-filter_complex", (
            f"[0:v]crop=ih*9/16:ih,scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT},setsar=1[v_scaled];"
            f"[v_scaled]subtitles={subtitles_path}:force_style='{subtitle_style}'[v];"
            f"[2:a]volume={config.MUSIC_VOLUME}[bgm];"
            "[1:a][bgm]amix=inputs=2:duration=first[a]"
        ),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
        "-c:a", "aac", "-b:a", "96k",
        "-shortest", str(output_path)
    ]

    logging.info("Executing FFmpeg command (low quality, fast preset)...")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate(timeout=180) # 3-minute timeout

        if process.returncode != 0:
            logging.error(f"--- FFmpeg command failed! ---\n{stderr}")
            return None
        
        logging.info(f"Final video saved to: {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        logging.error("--- FFmpeg command timed out after 3 minutes. ---")
        process.kill()
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None
