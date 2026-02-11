# project/main.py

import logging
import random
from datetime import datetime
from pathlib import Path

# --- Configuration and Setup ---
import config
import scheduler
from content.categories import CATEGORIES

# --- Import Core Modules ---
from generation.script_generator import generate_script
from generation.tts import generate_tts_audio
from generation.captions import generate_captions
from generation.video_builder import build_video
from posting.facebook import FacebookUploader
from cleanup import perform_cleanup

# --- Master Logging Configuration ---
# This sets up logging for the entire application run.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    handlers=[
        logging.FileHandler(config.BASE_DIR / "app.log"),
        logging.StreamHandler()
    ]
)


def setup():
    """Ensures all necessary directories from the config exist."""
    logging.info("--- Initializing Setup ---")
    for directory in config.REQUIRED_DIRS:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logging.info(f"Directory ensured: {directory}")
        except OSError as e:
            logging.critical(f"FATAL: Could not create required directory {directory}. Error: {e}")
            raise


def run_job():
    """
    Executes the entire video generation and posting pipeline once.
    """
    unique_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.info(f"========= STARTING NEW JOB | ID: {unique_id} =========")

    final_video_path = None
    try:
        # 1. INTELLIGENT CONTENT SELECTION (using scheduler)
        logging.info("--- Step 1: Selecting Content ---")
        category_name = scheduler.get_next_item('category', list(CATEGORIES.keys()))
        sub_theme = random.choice(CATEGORIES[category_name])

        # 2. GENERATION PIPELINE
        logging.info("--- Step 2: Generating Script ---")
        script_data = generate_script(category=category_name, sub_theme=sub_theme)
        if not script_data:
            raise Exception("Failed to generate script. Aborting job.")

        logging.info("--- Step 3: Generating TTS Audio ---")
        audio_path = generate_tts_audio(script_data['script'], unique_id)
        if not audio_path:
            raise Exception("Failed to generate TTS audio. Aborting job.")

        logging.info("--- Step 4: Generating Captions ---")
        subtitles_path = generate_captions(audio_path, unique_id)
        if not subtitles_path:
            raise Exception("Failed to generate captions. Aborting job.")

        # 3. VIDEO ASSEMBLY
        logging.info("--- Step 5: Building Final Video ---")
        final_video_path = build_video(audio_path, subtitles_path, unique_id)
        if not final_video_path:
            raise Exception("Failed to build final video. Aborting job.")

        # 4. POSTING
        logging.info("--- Step 6: Uploading to Facebook ---")
        uploader = FacebookUploader(
            page_id=config.FACEBOOK_PAGE_ID,
            page_access_token=config.FACEBOOK_PAGE_ACCESS_TOKEN
        )
        post_id = uploader.upload_and_publish(final_video_path)

        # 5. CLEANUP (ONLY ON SUCCESS)
        if post_id:
            logging.info(f"--- Step 7: Performing Cleanup for successful post ---")
            perform_cleanup(unique_id)
        else:
            logging.error("Upload failed. Skipping cleanup to allow for manual inspection of temp files.")
            raise Exception("Facebook upload failed. See logs for details.")

        logging.info("========= JOB COMPLETED SUCCESSFULLY =========")

    except Exception as e:
        logging.critical(f"An error occurred during the job execution: {e}")
        logging.critical("========= JOB FAILED =========")


if __name__ == '__main__':
    # This is the entry point when the script is run directly by cron.
    try:
        setup()
        run_job()
    except Exception as e:
        logging.critical(f"A critical error occurred in main execution block: {e}")