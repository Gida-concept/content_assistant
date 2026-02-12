# project/generation/tts.py
import logging
import subprocess
from pathlib import Path
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [TTSGenerator] - %(message)s')

def generate_tts_audio(script_text: str, unique_id: str) -> Path | None:
    logging.info(f"Starting TTS generation for ID: {unique_id}")
    
    try:
        output_filename = f"audio_{unique_id}.wav"
        output_path = config.TEMP_AUDIO_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean text for TTS
        processed_text = ' '.join(script_text.split()).replace('\n', ' ').strip()
        logging.info(f"Processing {len(processed_text)} characters for TTS...")

        # Call Piper command-line tool
        command = [
            "/opt/piper/piper",
            "--model", config.TTS_MODEL_PATH,
            "--output_file", str(output_path)
        ]
        
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send the text to piper via stdin
        stdout, stderr = process.communicate(input=processed_text, timeout=60)
        
        if process.returncode != 0:
            logging.error(f"Piper command failed with return code {process.returncode}")
            logging.error(f"Stderr: {stderr}")
            return None
        
        if not output_path.exists():
            logging.error("Piper did not create the output file.")
            return None

        logging.info(f"Successfully saved TTS audio to: {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"An error occurred during TTS generation: {e}")
        return None
