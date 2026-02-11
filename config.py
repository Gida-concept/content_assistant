# project/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# --- Security & Environment Loading ---
# Loads environment variables from a .env file for local development.
load_dotenv()

# --- API Keys ---
# Groq API Key for LLM (script generation) and Whisper (captions)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")

# --- Facebook API Credentials ---
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "YOUR_FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "YOUR_FACEBOOK_ACCESS_TOKEN")

# --- File & Directory Paths ---
BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
ASSETS_DIR = BASE_DIR / "assets"
BACKGROUND_VIDEOS_DIR = ASSETS_DIR / "videos"
BACKGROUND_MUSIC_DIR = ASSETS_DIR / "music"
TEMP_DIR = BASE_DIR / "temp"
TEMP_AUDIO_DIR = TEMP_DIR / "audio"
TEMP_SUBTITLES_DIR = TEMP_DIR / "subtitles"
TEMP_VIDEOS_DIR = TEMP_DIR / "videos"

# --- Content Generation Settings ---
# Groq model for script generation
LLM_MODEL = "llama3-70b-versatile"

# --- Kitten TTS (Local Library) Configuration ---
# The model name to be loaded by the KittenTTS library
TTS_MODEL_NAME = "KittenML/kitten-tts-nano-0.2"

# The specific voice to use. The 'm' voices are male.
# 'expr-voice-2-m' is a good choice for a calm, authoritative tone.
# Available voices: ['expr-voice-2-m', 'expr-voice-2-f', 'expr-voice-3-m',
#                   'expr-voice-3-f', 'expr-voice-4-m', 'expr-voice-4-f',
#                   'expr-voice-5-m', 'expr-voice-5-f']
TTS_VOICE_ID = "expr-voice-2-m"

# The sample rate required by the KittenTTS model for saving the audio file.
TTS_SAMPLE_RATE = 24000

# --- Video Generation Settings ---
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
MUSIC_VOLUME = 0.08 # 8% volume

# Caption settings for FFmpeg
CAPTION_FONT_SIZE = 60
CAPTION_FONT_COLOR = "white"
CAPTION_FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # A common path on Linux
# For Windows: "C:/Windows/Fonts/arialbd.ttf" (Arial Bold)
# For MacOS: "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
# IMPORTANT: Update this path to a valid BOLD font file on your system.
CAPTION_POSITION = f"x=(w-text_w)/2:y=h-th-({VIDEO_HEIGHT * 0.15})"

# --- System Health ---
REQUIRED_DIRS = [
    ASSETS_DIR, BACKGROUND_VIDEOS_DIR, BACKGROUND_MUSIC_DIR,
    TEMP_DIR, TEMP_AUDIO_DIR, TEMP_SUBTITLES_DIR, TEMP_VIDEOS_DIR, CONTENT_DIR,
]