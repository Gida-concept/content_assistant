# project/generation/tts.py

import logging
import soundfile as sf
import numpy as np
from pathlib import Path
import re

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

def split_into_sentences(text: str) -> list:
    """Split text into sentences, respecting periods, exclamation marks, and question marks."""
    # Use regex to split on sentence endings while preserving the punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter out empty strings
    return [s.strip() for s in sentences if s.strip()]

def generate_tts_audio(script_text: str, unique_id: str) -> Path | None:
    """
    Converts a text script into a .wav audio file using the pre-loaded KittenTTS model.
    Processes text in sentence chunks to avoid ONNX errors with long text.

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

        # Preprocess and limit text length
        max_chars = 5000
        processed_text = script_text[:max_chars] if len(script_text) > max_chars else script_text
        processed_text = processed_text.replace('\n', ' ').replace('\r', '')
        processed_text = ' '.join(processed_text.split())
        
        # Split into sentences to avoid ONNX model errors with long text
        sentences = split_into_sentences(processed_text)
        logging.info(f"Split script into {len(sentences)} sentences for processing.")
        
        # Generate audio for each sentence
        audio_chunks = []
        for i, sentence in enumerate(sentences, 1):
            logging.info(f"Generating audio for sentence {i}/{len(sentences)}...")
            audio_chunk = tts_model.generate(sentence, voice=config.TTS_VOICE_ID)
            if audio_chunk is None or len(audio_chunk) == 0:
                logging.warning(f"Empty audio returned for sentence {i}, skipping.")
                continue
            audio_chunks.append(audio_chunk)
        
        if not audio_chunks:
            raise ValueError("No audio data was generated from any sentence.")
        
        # Concatenate all audio chunks
        logging.info("Concatenating audio chunks...")
        final_audio = np.concatenate(audio_chunks)
        
        # Save the final audio
        logging.info("Writing final audio to .wav file...")
        sf.write(output_path, final_audio, config.TTS_SAMPLE_RATE)

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

    test_script = "This is a test. The system splits text into sentences. Each sentence is processed separately. This prevents ONNX errors."
    test_id = "standalone_test_chunking"
    
    audio_path = generate_tts_audio(test_script, test_id)

    if audio_path and audio_path.exists():
        print(f"\n✅ --- TTS AUDIO GENERATED SUCCESSFULLY --- ✅")
        print(f"File saved at: {audio_path}")
    else:
        print(f"\n❌ --- TTS AUDIO GENERATION FAILED --- ❌")
