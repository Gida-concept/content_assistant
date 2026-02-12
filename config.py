# project/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "YOUR_FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "YOUR_FACEBOOK_ACCESS_TOKEN")

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
ASSETS_DIR = BASE_DIR / "assets"
BACKGROUND_VIDEOS_DIR = ASSETS_DIR / "videos"
BACKGROUND_MUSIC_DIR = ASSETS_DIR / "music"
TEMP_DIR = BASE_DIR / "temp"
TEMP_AUDIO_DIR = TEMP_DIR / "audio"
TEMP_SUBTITLES_DIR = TEMP_DIR / "subtitles"
TEMP_VIDEOS_DIR = TEMP_DIR / "videos"

LLM_MODEL = "llama-3.3-70b-versatile"

# --- Kitten TTS (Local Library) Configuration ---
TTS_MODEL_NAME = "KittenML/kitten-tts-nano-0.2"
TTS_VOICE_ID = "expr-voice-2-m"
TTS_SAMPLE_RATE = 24000

# --- Video Generation Settings ---
# Low-resolution for faster processing on VPS
VIDEO_WIDTH = 240
VIDEO_HEIGHT = 426

# Caption settings for low-res video
CAPTION_FONT_SIZE = 20
CAPTION_FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Volume settings. 1.0 is 100%. Boost voice, lower music.
VOICE_VOLUME = 1.5
MUSIC_VOLUME = 0.25

REQUIRED_DIRS = [
    ASSETS_DIR, BACKGROUND_VIDEOS_DIR, BACKGROUND_MUSIC_DIR,
    TEMP_DIR, TEMP_AUDIO_DIR, TEMP_SUBTITLES_DIR, TEMP_VIDEOS_DIR, CONTENT_DIR,
]


