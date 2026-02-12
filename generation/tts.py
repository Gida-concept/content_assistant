# project/generation/tts.py
import logging
import wave
from pathlib import Path
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [TTSGenerator] - %(message)s')

# --- Load Piper TTS using the correct, updated API ---
try:
    from piper.voice import PiperVoice
    
    # The correct way to load the model
    logging.info(f"Loading Piper TTS model from: {config.TTS_MODEL_PATH}")
    voice = PiperVoice(
        onnx_path=config.TTS_MODEL_PATH,
        config_path=f"{config.TTS_MODEL_PATH}.json"
    )
    logging.info("Piper TTS model loaded successfully.")

except Exception as e:
    logging.error(f"FATAL: Failed to load Piper model: {e}")
    voice = None

def generate_tts_audio(script_text: str, unique_id: str) -> Path | None:
    if not voice:
        logging.error("Cannot generate audio: Piper TTS model is not available.")
        return None

    logging.info(f"Starting TTS generation for ID: {unique_id}")
    try:
        output_filename = f"audio_{unique_id}.wav"
        output_path = config.TEMP_AUDIO_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean text for TTS
        processed_text = ' '.join(script_text.split()).replace('\n', ' ').strip()
        logging.info(f"Processing {len(processed_text)} characters for TTS...")

        # Piper's synthesize method now directly writes to a file path
        voice.synthesize(processed_text, str(output_path))

        logging.info(f"Successfully saved TTS audio to: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"An error occurred during TTS generation: {e}")
        return None
