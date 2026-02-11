# project/generation/tts.py

import logging
import soundfile as sf
from pathlib import Path

# Import project-specific modules
import config

# --- Library and Model Initialization ---
try:
    from kittentts import KittenTTS
except ImportError:
    logging.critical("KittenTTS library not found. Please install it via pip.")
    KittenTTS = None

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [TTSGenerator] - %(message)s')

# Initialize the model once when the module is loaded
tts_model = None
if KittenTTS:
    try:
        logging.info(f"Loading KittenTTS model: {config.TTS_MODEL_NAME}...")
        tts_model = KittenTTS(config.TTS_MODEL_NAME)
        logging.info("KittenTTS model loaded successfully.")
    except Exception as e:
        logging.error(f"FATAL: Failed to load KittenTTS model. Error: {e}")
        tts_model = None

def generate_tts_audio(script_text: str, unique_id: str) -> Path | None:
    """
    Converts a text script into a .wav audio file using the pre-loaded KittenTTS model.

    Args:
        script_text: The text content to be converted to speech.
        unique_id: A unique identifier for the current video job, used for the filename.

    Returns:
        A Path object to the generated audio file on success, otherwise None.
    """
    if not tts_model:
        logging.error("Cannot generate audio: KittenTTS model is not available.")
        return None

    logging.info(f"Starting TTS generation for ID: {unique_id}")

    try:
        output_filename = f"audio_{unique_id}.wav"
        output_path = config.TEMP_AUDIO_DIR / output_filename
        config.TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

        # Preprocess text for KittenTTS compatibility
        max_chars = 5000
        processed_text = script_text[:max_chars] if len(script_text) > max_chars else script_text
        
        # Clean the text: remove newlines, normalize spaces, and remove characters
        # that might confuse the underlying ONNX model.
        processed_text = processed_text.replace('\n', ' ').replace('\r', '')
        processed_text = ' '.join(processed_text.split())
        
        logging.info(f"Processing {len(processed_text)} characters for TTS with voice ID: '{config.TTS_VOICE_ID}'...")

        # Generate the raw audio data from the preprocessed script text
        audio_data = tts_model.generate(processed_text, voice=config.TTS_VOICE_ID)

        if audio_data is None:
            raise ValueError("KittenTTS model returned no audio data.")

        logging.info("Audio data generated. Writing to .wav file...")
        sf.write(output_path, audio_data, config.TTS_SAMPLE_RATE)

        logging.info(f"Successfully saved TTS audio to: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"An error occurred during TTS generation or file saving: {e}")
        return None

# --- Standalone Test Block ---
if __name__ == '__main__':
    print("Running tts.py in standalone mode for testing...")
    for directory in config.REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)

    test_script = "This is a test of the Kitten Text to Speech engine. This version includes text preprocessing to remove newlines and extra spaces, which should prevent ONNX model errors."
    test_id = "standalone_test_001"
    
    audio_path = generate_tts_audio(test_script, test_id)

    if audio_path and audio_path.exists():
        print(f"\n✅ --- TTS AUDIO GENERATED SUCCESSFULLY --- ✅")
        print(f"File saved at: {audio_path}")
    else:
        print(f"\n❌ --- TTS AUDIO GENERATION FAILED --- ❌")
        print("Check logs for errors.")
