# project/posting/facebook.py

import logging
import random
import requests
from pathlib import Path

# Import project-specific modules
import config
from content.seo import CAPTION_TEMPLATE, HASHTAG_GROUPS

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [FacebookUploader] - %(message)s')

# --- Constants for Facebook Graph API ---
GRAPH_API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class FacebookUploader:
    """Handles the two-step process of uploading a video to Facebook Reels."""

    def __init__(self, page_id: str, page_access_token: str):
        """
        Initializes the uploader with Facebook credentials.

        Args:
            page_id: The ID of the Facebook Page to post to.
            page_access_token: The long-lived page access token.
        """
        if not all([page_id, page_access_token]) or "YOUR_FACEBOOK" in page_id:
            raise ValueError("Facebook Page ID or Access Token is not configured.")

        self.page_id = page_id
        self.access_token = page_access_token
        self.base_reels_url = f"{BASE_URL}/{self.page_id}/video_reels"
        logging.info("FacebookUploader initialized.")

    def _generate_caption(self) -> str:
        """Generates the final post caption including a random hashtag group."""
        random_hashtags = random.choice(HASHTAG_GROUPS)
        hashtag_string = " ".join(random_hashtags)
        return f"{CAPTION_TEMPLATE}\n\n{hashtag_string}"

    def _start_upload_session(self) -> str | None:
        """
        Step 1: Initializes the upload session with Facebook.

        Returns:
            The upload session ID if successful, otherwise None.
        """
        logging.info("Step 1: Initializing Reels upload session...")
        params = {
            "upload_phase": "start",
            "access_token": self.access_token
        }
        try:
            response = requests.post(self.base_reels_url, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

            data = response.json()
            video_id = data.get("video_id")
            if not video_id:
                logging.error(f"Failed to get video_id from start phase. Response: {data}")
                return None

            logging.info(f"Upload session started. Video ID: {video_id}")
            return video_id
        except requests.exceptions.RequestException as e:
            logging.error(f"Error starting upload session: {e}")
            logging.error(f"Response Body: {e.response.text if e.response else 'No Response'}")
            return None

    def _upload_video_chunk(self, video_id: str, video_path: Path) -> bool:
        """
        Step 2: Uploads the video file to the initialized session.

        Args:
            video_id: The ID of the upload session (returned from step 1).
            video_path: The path to the video file to upload.

        Returns:
            True if the upload was successful, False otherwise.
        """
        logging.info(f"Step 2: Uploading video file '{video_path.name}'...")
        upload_url = f"https://graph-video.facebook.com/{GRAPH_API_VERSION}/{video_id}"

        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "file_offset": "0"
        }

        try:
            with open(video_path, "rb") as f:
                video_data = f.read()

            response = requests.post(upload_url, headers=headers, data=video_data, timeout=600)  # 10-min timeout
            response.raise_for_status()

            data = response.json()
            if not data.get("success"):
                logging.error(f"Video chunk upload failed. Response: {data}")
                return False

            logging.info("Video file uploaded successfully.")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during video file upload: {e}")
            logging.error(f"Response Body: {e.response.text if e.response else 'No Response'}")
            return False

    def _publish_reel(self, video_id: str, caption: str) -> str | None:
        """
        Step 3: Publishes the uploaded video as a Reel with a caption.

        Args:
            video_id: The ID of the successfully uploaded video.
            caption: The text to be used as the Reel's caption.

        Returns:
            The post ID of the published Reel on success, otherwise None.
        """
        logging.info("Step 3: Publishing the Reel...")
        params = {
            "video_id": video_id,
            "upload_phase": "finish",
            "video_state": "PUBLISHED",
            "description": caption,
            "access_token": self.access_token
        }
        try:
            response = requests.post(self.base_reels_url, params=params)
            response.raise_for_status()

            data = response.json()
            post_id = data.get("id")
            if not post_id:
                logging.error(f"Failed to get post ID after publishing. Response: {data}")
                return None

            logging.info(f"Reel published successfully! Post ID: {post_id}")
            return post_id
        except requests.exceptions.RequestException as e:
            logging.error(f"Error publishing Reel: {e}")
            logging.error(f"Response Body: {e.response.text if e.response else 'No Response'}")
            return None

    def upload_and_publish(self, video_path: Path) -> str | None:
        """
        Orchestrates the full upload and publish workflow.

        Args:
            video_path: The path to the final video to be uploaded.

        Returns:
            The final post ID if the entire process is successful, otherwise None.
        """
        logging.info(f"--- Starting Facebook Reel Upload for: {video_path.name} ---")

        # Step 1: Start session
        video_id = self._start_upload_session()
        if not video_id:
            return None

        # Step 2: Upload file
        if not self._upload_video_chunk(video_id, video_path):
            return None

        # Step 3: Publish with caption
        caption = self._generate_caption()
        logging.info(f"Using caption:\n{caption}")
        post_id = self._publish_reel(video_id, caption)

        if post_id:
            logging.info(f"--- Upload process completed successfully. Post URL: https://www.facebook.com/{post_id} ---")
            return post_id
        else:
            logging.error("--- Upload process failed at the publishing step. ---")
            return None


# --- Standalone Test Block ---
if __name__ == '__main__':
    print("Running facebook.py in standalone mode for testing...")
    print("This will attempt to upload a dummy video file to your Facebook page.")

    # Create a dummy video file for testing
    dummy_video_dir = config.TEMP_VIDEOS_DIR
    dummy_video_dir.mkdir(parents=True, exist_ok=True)
    dummy_video_path = dummy_video_dir / "test_upload.mp4"

    # Check if a real video exists from a previous step, otherwise create a tiny dummy
    if not dummy_video_path.exists():
        print("Creating a dummy black screen video for testing upload...")
        # Use FFmpeg to create a 1-second black video if none exists
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1",
                "-f", "lavfi", "-i", "anullsrc=r=44100", "-shortest",
                "-c:v", "libx264", "-c:a", "aac", str(dummy_video_path)
            ], check=True, capture_output=True)
            print(f"Dummy video created at {dummy_video_path}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print("\n❌ --- FAILED TO CREATE DUMMY VIDEO --- ❌")
            print("FFmpeg might not be installed or accessible.")
            print(f"Error: {e}")
            exit()  # Exit the test if we can't create the file

    try:
        uploader = FacebookUploader(
            page_id=config.FACEBOOK_PAGE_ID,
            page_access_token=config.FACEBOOK_PAGE_ACCESS_TOKEN
        )
        post_id = uploader.upload_and_publish(dummy_video_path)

        if post_id:
            print(f"\n✅ --- UPLOAD AND PUBLISH SUCCESSFUL --- ✅")
            print(f"Check your Facebook page for the new Reel. Post ID: {post_id}")
        else:
            print("\n❌ --- UPLOAD FAILED --- ❌")
            print("Check logs for errors. Common issues include:")
            print("- Invalid/expired Page Access Token.")
            print("- Missing API permissions (pages_manage_posts, publish_video).")
            print("- Incorrect Page ID.")
    except ValueError as e:
        print(f"\n❌ --- CONFIGURATION ERROR --- ❌")
        print(f"Error: {e}")
        print("Please ensure FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN are set in your .env file.")