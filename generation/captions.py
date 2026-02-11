# project/generation/captions.py

import logging
import json
from pathlib import Path

# Import project-specific modules
import config
from groq import Groq

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [CaptionsGenerator] - %(message)s')

# --- Groq Client Initialization ---
try:
    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        raise ValueError("GROQ_API_KEY is not configured.")
    groq_client = Groq(api_key=config.GROQ_API_KEY)
    logging.info("Groq client for Whisper initialized successfully.")
except (ValueError, Exception) as e:
    logging.error(f"Failed to initialize Groq client: {e}")
    groq_client = None

def _format_time(seconds: float) -> str:
    """Formats seconds into SRT time format HH:MM:SS,ms"""
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def _to_srt(segments: list) -> str:
    """Converts Whisper's verbose_json segments into an SRT formatted string."""
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = _format_time(segment['start'])
        end_time = _format_time(segment['end'])
        text = segment['text'].strip()
        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_content

def generate_captions(audio_file_path: Path, unique_id: str) -> Path | None:
    """
    Transcribes an audio file using Groq's Whisper model (verbose_json)
    and manually builds and saves an .srt file.
    """
    if not groq_client:
        logging.error("Cannot generate captions: Groq client is not available.")
        return None

    if not audio_file_path or not audio_file_path.exists():
        logging.error(f"Audio file not found at: {audio_file_path}. Cannot generate captions.")
        return None

    logging.info(f"Starting caption generation for audio file: {audio_file_path.name}")

    try:
        output_filename = f"subtitles_{unique_id}.srt"
        output_path = config.TEMP_SUBTITLES_DIR / output_filename # This is the corrected line
        config.TEMP_SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)

        with open(audio_file_path, "rb") as audio_file:
            logging.info("Uploading audio to Groq Whisper API for transcription...")
            transcription = groq_client.audio.transcriptions.create(
                file=(audio_file_path.name, audio_file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        # The transcription object is now a JSON-like object, not a raw string
        srt_content = _to_srt(transcription.segments)
        
        output_path.write_text(srt_content, encoding='utf-8')

        logging.info(f"Successfully built and saved SRT captions to: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"An error occurred during Whisper transcription: {e}")
        return None

# --- Standalone Test Block ---
if __name__ == '__main__':
    from generation.tts import generate_tts_audio
    print("Running captions.py in standalone mode for testing...")
    
    for directory in config.REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        
    test_script = "This tests the manual SRT generation from verbose json. This is the corrected file."
    test_id = "standalone_caption_test_001"

    audio_path = generate_tts_audio(test_script, test_id)
    if audio_path:
        captions_path = generate_captions(audio_path, test_id)
        if captions_path and captions_path.exists():
            print(f"\n✅ --- CAPTIONS GENERATED SUCCESSFULLY --- ✅")
            print(f"SRT file saved at: {captions_path}")
            print("\n--- SRT File Content ---")
            print(captions_path.read_text())
        else:
            print("\n❌ --- CAPTION GENERATION FAILED --- ❌")
    else:
        print("\n❌ --- FAILED TO GENERATE TEST AUDIO --- ❌")
