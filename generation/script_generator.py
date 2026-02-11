# project/generation/script_generator.py

import os
import random
import logging
from groq import Groq

# Import project-specific modules
import config
from content.categories import CATEGORIES
from content.prompt import HOOK_GENERATION_PROMPT, SCRIPT_GENERATION_PROMPT

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [ScriptGenerator] - %(message)s')

# --- Groq Client Initialization ---
# Initialize the client once to be reused in all functions.
# This is more efficient than creating a new client for every call.
try:
    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        raise ValueError("GROQ_API_KEY is not configured.")
    groq_client = Groq(api_key=config.GROQ_API_KEY)
    logging.info("Groq client initialized successfully.")
except (ValueError, Exception) as e:
    logging.error(f"Failed to initialize Groq client: {e}")
    groq_client = None


def _call_groq_api(prompt: str, model: str, max_tokens: int = 2048, temperature: float = 0.7) -> str:
    """
    A helper function to call the Groq API and handle responses and errors.

    Args:
        prompt: The full prompt to send to the LLM.
        model: The model to use for the completion.
        max_tokens: The maximum number of tokens for the response.
        temperature: The creativity of the response.

    Returns:
        The text content from the LLM's response.

    Raises:
        ConnectionError: If the Groq client is not initialized.
        Exception: For API errors or empty responses.
    """
    if not groq_client:
        raise ConnectionError("Groq client is not available. Check API key and initialization.")

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response_text = chat_completion.choices[0].message.content
        if not response_text:
            raise ValueError("LLM returned an empty response.")
        return response_text.strip()
    except Exception as e:
        logging.error(f"An error occurred during the Groq API call: {e}")
        raise


def generate_script() -> dict | None:
    """
    Orchestrates the two-step script generation process.

    1. Selects a random category and sub-theme.
    2. Generates a dynamic, unique hook using the first LLM call.
    3. Generates the full script using the hook and a second LLM call.

    Returns:
        A dictionary containing the 'script', 'category', and 'sub_theme' if successful,
        otherwise None.
    """
    logging.info("--- Starting Script Generation Process ---")

    try:
        # 1. Select Content Core
        category = random.choice(list(CATEGORIES.keys()))
        sub_theme = random.choice(CATEGORIES[category])
        logging.info(f"Selected Topic -> Category: '{category}', Sub-theme: '{sub_theme}'")

        # 2. Generate Dynamic Hook (LLM Call #1)
        logging.info("Generating dynamic hook...")
        hook_prompt = HOOK_GENERATION_PROMPT.format(category=category, sub_theme=sub_theme)
        generated_hook = _call_groq_api(hook_prompt, config.LLM_MODEL, max_tokens=150, temperature=0.8)
        logging.info(f"Generated Hook: '{generated_hook}'")

        # 3. Generate Full Script (LLM Call #2)
        logging.info("Generating full script from hook...")
        script_prompt = SCRIPT_GENERATION_PROMPT.format(
            category=category,
            sub_theme=sub_theme,
            hook=generated_hook
        )
        final_script = _call_groq_api(script_prompt, config.LLM_MODEL, max_tokens=2048, temperature=0.7)
        logging.info("Successfully generated final script.")

        # 4. Return all generated content in a structured dictionary
        return {
            "script": final_script,
            "category": category,
            "sub_theme": sub_theme
        }

    except (ConnectionError, ValueError, Exception) as e:
        logging.error(f"Script generation process failed: {e}")
        return None


# --- Standalone Test Block ---
if __name__ == '__main__':
    # This block allows you to run this file directly to test script generation
    # without running the entire video creation pipeline.
    print("Running script_generator.py in standalone mode for testing...")

    result = generate_script()

    if result:
        print("\n✅ --- SCRIPT GENERATED SUCCESSFULLY --- ✅")
        print(f"\nCATEGORY: {result['category']}")
        print(f"SUB-THEME: {result['sub_theme']}")
        print("\n--- SCRIPT TEXT ---")
        print(result['script'])
    else:
        print("\n❌ --- SCRIPT GENERATION FAILED --- ❌")
        print("Check the logs above for error details. Ensure your GROQ_API_KEY is correct in your .env file.")