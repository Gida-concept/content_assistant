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
    
    # Verify all files exist
    if not background_video_path or not background_music_path:
        logging.error("Could not select background assets.")
        return None
    if not audio_path.exists():
        logging.error(f"TTS audio file does not exist: {audio_path}")
        return None
    if not subtitles_path.exists():
        logging.error(f"Subtitles file does not exist: {subtitles_path}")
        return None

    logging.info(f"Background video: {background_video_path}")
    logging.info(f"TTS audio: {audio_path} (size: {audio_path.stat().st_size} bytes)")
    logging.info(f"Background music: {background_music_path}")
    logging.info(f"Subtitles: {subtitles_path}")

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
            f"[1:a]volume={config.VOICE_VOLUME}[voice];"
            f"[2:a]volume={config.MUSIC_VOLUME}[music];"
            "[voice][music]amix=inputs=2:duration=first[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(final_video_path)
    ]

    # Log the exact command
    logging.info("=" * 80)
    logging.info("FFMPEG COMMAND:")
    logging.info(" ".join(str(c) for c in command))
    logging.info("=" * 80)

    try:
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding='utf-8'
        )
        stdout, stderr = process.communicate(timeout=180)

        # Save FFmpeg output to a log file for inspection
        log_file = config.TEMP_DIR / f"ffmpeg_log_{unique_id}.txt"
        with open(log_file, 'w') as f:
            f.write("=== FFMPEG STDOUT ===\n")
            f.write(stdout)
            f.write("\n\n=== FFMPEG STDERR ===\n")
            f.write(stderr)
        logging.info(f"FFmpeg output saved to: {log_file}")

        # Print stderr to our log (this is where FFmpeg prints progress and errors)
        if stderr:
            logging.info("FFmpeg stderr output:")
            for line in stderr.split('\n')[-30:]:  # Print last 30 lines
                logging.info(f"  {line}")

        if process.returncode != 0:
            logging.error(f"FFmpeg FAILED with return code: {process.returncode}")
            logging.error("Full error output saved to log file above.")
            return None
        
        # Verify the output file exists and has a reasonable size
        if not final_video_path.exists():
            logging.error("FFmpeg reported success but output file was not created!")
            return None
            
        file_size = final_video_path.stat().st_size
        logging.info(f"Output video size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
        
        if file_size < 100000:  # Less than 100KB is suspiciously small
            logging.warning(f"Output file is very small ({file_size} bytes). Video may be corrupted.")
        
        logging.info(f"Final video successfully created at: {final_video_path}")
        return final_video_path
        
    except subprocess.TimeoutExpired:
        logging.error("FFmpeg command timed out after 3 minutes.")
        process.kill()
        return None
    except Exception as e:
        logging.error(f"Unexpected error during FFmpeg execution: {e}")
        return None
