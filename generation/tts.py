# project/generation/tts.py

import logging
import soundfile as sf
from pathlib import Path

# Import project-specific modules
import config

# --- Library and Model Initialization ---
# This section handles the import and loading of the KittenTTS model.
# It's structured to fail gracefully if the library isn't installed.

try:
    from kittentts import KittenTTS
except ImportError:
    logging.critical("KittenTTS library not found. Please install it via pip.")
    KittenTTS = None  # Allows the script to run without crashing, but functions will fail.

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [TTSGenerator] - %(message)s')

# Initialize the model once when the module is loaded.
# This is far more efficient than reloading the model every time the function is called.
tts_model = None
if KittenTTS:
    try:
        logging.info(f"Loading KittenTTS model: {config.TTS_MODEL_NAME}...")
        tts_model = KittenTTS(config.TTS_MODEL_NAME)
        logging.info("KittenTTS model loaded successfully.")
    except Exception as e:
        logging.error(f"FATAL: Failed to load KittenTTS model. Error: {e}")
        # tts_model remains None, functions will check for this and exit.

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
        # Define the output path in the temporary audio directory
        output_filename = f"audio_{unique_id}.wav"
        output_path = config.TEMP_AUDIO_DIR / output_filename

        # Ensure the temporary directory exists before writing
        config.TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

        logging.info(f"Generating audio with voice ID: '{config.TTS_VOICE_ID}'...")

        # Generate the raw audio data from the script text
        audio_data = tts_model.generate(script_text, voice=config.TTS_VOICE_ID)

        if audio_data is None:
            raise ValueError("KittenTTS model returned no audio data.")

        logging.info("Audio data generated. Writing to .wav file...")

        # Save the audio data to a .wav file using the correct sample rate
        sf.write(output_path, audio_data, config.TTS_SAMPLE_RATE)

        logging.info(f"Successfully saved TTS audio to: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"An error occurred during TTS generation or file saving: {e}")
        return None

# --- Standalone Test Block ---
if __name__ == '__main__':
    # This allows for direct testing of the TTS module.
    print("Running tts.py in standalone mode for testing...")

    # Create required directories for the test to run smoothly
    for directory in config.REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)

    test_script = """
    This is a test of the Kitten Text to Speech engine.
    The system should use the calm authority voice defined in the configuration file.
    It will generate a WAV file and save it to the temporary audio directory.
    This demonstrates that the core audio generation component is working correctly.
    """
    test_id = "standalone_test_001"

    # Call the main function
    audio_path = generate_tts_audio(test_script, test_id)

    if audio_path and audio_path.exists():
        print("\n✅ --- TTS AUDIO GENERATED SUCCESSFULLY --- ✅")
        print(f"File saved at: {audio_path}")
        print("Please listen to the file to verify audio quality and voice selection.")
    else:
        print("\n❌ --- TTS AUDIO GENERATION FAILED --- ❌")
        print("Check the logs for errors. Common issues include:")
        print("- KittenTTS or soundfile not being installed correctly.")
        print("- An invalid model name or voice ID in config.py.")
        