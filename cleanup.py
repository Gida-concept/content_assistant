# project/cleanup.py

import logging
from pathlib import Path

# Import project-specific modules
import config

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [Cleanup] - %(message)s')


def perform_cleanup(unique_id: str):
    """
    Deletes all temporary files associated with a specific video generation job.

    This function searches for files in the temporary directories that contain
    the unique_id and safely deletes them.

    Args:
        unique_id: The unique identifier for the job run.
    """
    logging.info(f"--- Starting Cleanup Process for ID: {unique_id} ---")

    # List of files to delete, constructed using the unique_id
    files_to_delete = [
        config.TEMP_AUDIO_DIR / f"audio_{unique_id}.wav",
        config.TEMP_SUBTITLES_DIR / f"subtitles_{unique_id}.srt",
        config.TEMP_VIDEOS_DIR / f"final_video_{unique_id}.mp4"
    ]

    deleted_count = 0
    for file_path in files_to_delete:
        try:
            if file_path.exists():
                file_path.unlink()  # This deletes the file
                logging.info(f"Deleted temporary file: {file_path}")
                deleted_count += 1
            else:
                # This is not an error, just means the file wasn't created or was already cleaned up.
                logging.warning(f"Cleanup target not found (may have failed earlier): {file_path}")
        except OSError as e:
            logging.error(f"Error deleting file {file_path}: {e}")

    logging.info(f"Cleanup complete. Deleted {deleted_count} file(s) for ID: {unique_id}.")


# --- Standalone Test Block ---
if __name__ == '__main__':
    print("Running cleanup.py in standalone mode for testing...")

    # For testing, we'll create some dummy files to ensure the cleanup works.
    test_id = "standalone_cleanup_test_001"

    # Create required directories
    for directory in config.REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)

    dummy_files_to_create = [
        config.TEMP_AUDIO_DIR / f"audio_{test_id}.wav",
        config.TEMP_SUBTITLES_DIR / f"subtitles_{test_id}.srt",
        config.TEMP_VIDEOS_DIR / f"final_video_{test_id}.mp4",
        # Create an unrelated file to ensure it's NOT deleted
        config.TEMP_DIR / "do_not_delete.txt"
    ]

    print(f"\nCreating dummy files for test ID: {test_id}")
    for file_path in dummy_files_to_create:
        file_path.touch()  # Creates an empty file
        print(f"  - Created: {file_path}")

    # Verify files exist before cleanup
    for file_path in dummy_files_to_create:
        assert file_path.exists(), f"Failed to create dummy file {file_path}"

    print("\nRunning cleanup function...")
    perform_cleanup(test_id)

    # Verify the correct files were deleted
    print("\nVerifying cleanup results...")

    success = True
    # Check that targeted files are gone
    for file_path in dummy_files_to_create[:3]:  # Only check the first 3
        if file_path.exists():
            print(f"❌ FAILED: File was not deleted: {file_path}")
            success = False
        else:
            print(f"✅ OK: File successfully deleted: {file_path.name}")

    # Check that the unrelated file was NOT deleted
    unrelated_file = dummy_files_to_create[3]
    if unrelated_file.exists():
        print(f"✅ OK: Unrelated file was not deleted: {unrelated_file.name}")
        unrelated_file.unlink()  # Clean up the test file
    else:
        print(f"❌ FAILED: Unrelated file was mistakenly deleted: {unrelated_file.name}")
        success = False

    if success:
        print("\n✅ --- CLEANUP TEST SUCCESSFUL --- ✅")
    else:
        print("\n❌ --- CLEANUP TEST FAILED --- ❌")