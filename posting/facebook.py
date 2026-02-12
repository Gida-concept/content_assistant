# project/posting/facebook.py
import logging, random, requests, json
from pathlib import Path
import config
from content.seo import CAPTION_TEMPLATE, HASHTAG_GROUPS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [FacebookUploader] - %(message)s')
BASE_URL = f"https://graph.facebook.com/v19.0"

class FacebookUploader:
    def __init__(self, page_id: str, page_access_token: str):
        if not all([page_id, page_access_token]):
            raise ValueError("Facebook creds missing.")
        self.page_id = page_id
        self.access_token = page_access_token
        self.base_reels_url = f"{BASE_URL}/{self.page_id}/video_reels"

    def _generate_caption(self) -> str:
        hashtag_string = " ".join(random.choice(HASHTAG_GROUPS))
        raw_caption = f"{CAPTION_TEMPLATE} {hashtag_string}"
        # STRICTLY remove all newlines
        return raw_caption.replace('\n', ' ').replace('\r', '').strip()

    def upload_and_publish(self, video_path: Path) -> str | None:
        logging.info(f"--- Starting Facebook Reel Upload ---")
        
        # 1. Start Session
        try:
            start_resp = requests.post(self.base_reels_url, params={"upload_phase": "start", "access_token": self.access_token}).json()
            video_id = start_resp.get("video_id")
            if not video_id:
                logging.error(f"Start session failed: {start_resp}")
                return None
        except Exception as e:
            logging.error(f"Error starting session: {e}")
            return None

        # 2. Upload File
        try:
            with open(video_path, "rb") as f:
                requests.post(f"https://graph-video.facebook.com/{video_id}", headers={"Authorization": f"OAuth {self.access_token}"}, data=f, timeout=600).raise_for_status()
            logging.info("Video file uploaded.")
        except Exception as e:
            logging.error(f"Upload failed: {e}")
            return None

        # 3. Publish
        caption = self._generate_caption()
        logging.info(f"Caption: {caption}")
        try:
            pub_resp = requests.post(self.base_reels_url, params={
                "video_id": video_id, "upload_phase": "finish", "video_state": "PUBLISHED",
                "description": caption, "access_token": self.access_token
            })
            pub_resp.raise_for_status()
            post_id = pub_resp.json().get("id")
            logging.info(f"Reel published! Post ID: {post_id}")
            return post_id
        except Exception as e:
            logging.error(f"Publish failed: {e}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Response: {e.response.text}")
            return None
