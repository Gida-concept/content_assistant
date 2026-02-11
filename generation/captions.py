# project/generation/captions.py

import logging
from pathlib import Path

# Import project-specific modules
import config
from groq import Groq

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [CaptionsGenerator] - %(message)s')

# --- Groq Client Initialization ---
# Re-initializing the client here for modularity. This allows this script
# to be run independently for testing.
try:
    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        raise ValueError("GROQ_API_KEY is not configured.")
    groq_client = Groq(api_key=config.GROQ_API_KEY)
    logging.info("Groq client for Whisper initialized successfully.")
except (ValueError, Exception) as e:
    logging.error(f"Failed to initialize Groq client: {e}")
    groq_client = None


def generate_captions(audio_file_path: Path, unique_id: str) -> Path | None:
    """
    Transcribes an audio file using Groq's Whisper model and saves it as an .srt file.

    Args:
        audio_file_path: The Path object pointing to the generated .wav audio file.
        unique_id: The unique identifier for the current video job, for the filename.

    Returns:
        A Path object to the generated .srt subtitle file on success, otherwise None.
    """
    if not groq_client:
        logging.error("Cannot generate captions: Groq client is not available.")
        return None

    if not audio_file_path or not audio_file_path.exists():
        logging.error(f"Audio file not found at: {audio_file_path}. Cannot generate captions.")
        return None

    logging.info(f"Starting caption generation for audio file: {audio_file_path.name}")

    try:
        # Define the output path in the temporary subtitles directory
        output_filename = f"subtitles_{unique_id}.srt"
        output_path = config.TEMP_SUBTITLES_DIR / output_filename

        # Ensure the temporary directory exists
        config.TEMP_SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)

        # Open the audio file in binary read mode for the API
        with open(audio_file_path, "rb") as audio_file:
            logging.info("Uploading audio to Groq Whisper API for transcription...")

            # Requesting 'srt' format directly from the API is highly efficient.
            # whisper-large-v3 is the most accurate model.
            transcription = groq_client.audio.transcriptions.create(
                file=(audio_file_path.name, audio_file.read()),
                model="whisper-large-v3",
                response_format="srt"
            )

        # The API returns the complete SRT content as a single string
        srt_content = transcription

        # Write the SRT content to the output file
        output_path.write_text(srt_content, encoding='utf-8')

        logging.info(f"Successfully saved SRT captions to: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"An error occurred during Whisper transcription: {e}")
        return None


# --- Standalone Test Block ---
if __name__ == '__main__':
    # This block tests the caption generation by first creating a sample audio file.
    from generation.tts import generate_tts_audio  # Import the TTS function

    print("Running captions.py in standalone mode for testing...")
    print("This will first generate a test audio file, then transcribe it.")

    # Create required directories for the test
    for directory in config.REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)

    test_script = "This is a test of the caption generation system. The Whisper API should accurately transcribe this sentence into an SRT file, complete with timing information. This ensures the entire captioning pipeline is functional."
    test_id = "standalone_caption_test_001"

    # 1. Generate a test audio file first
    audio_path = generate_tts_audio(test_script, test_id)

    if audio_path:
        print(f"Test audio generated: {audio_path}")
        # 2. Now, generate captions from that audio file
        captions_path = generate_captions(audio_path, test_id)

        if captions_path and captions_path.exists():
            print("\n✅ --- CAPTIONS GENERATED SUCCESSFULLY --- ✅")
            print(f"SRT file saved at: {captions_path}")
            print("\n--- SRT File Content ---")
            print(captions_path.read_text())
        else:
            print("\n❌ --- CAPTION GENERATION FAILED --- ❌")
            print("Check logs for errors. Ensure your Groq API key is valid.")
    else:
        print("\n❌ --- FAILED TO GENERATE TEST AUDIO --- ❌")
        print("Cannot proceed with caption test. Check the TTS module first.")