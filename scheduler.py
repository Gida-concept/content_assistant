# project/scheduler.py

import json
import logging
import random
from pathlib import Path

import config
from content.categories import CATEGORIES

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [Scheduler] - %(message)s')

# The file where we store the history of used items
HISTORY_FILE = config.BASE_DIR / "run_history.json"
# How many recent items to remember and avoid repeating
CATEGORY_COOLDOWN = 5  # Avoid the last 5 categories
ASSET_COOLDOWN = 10  # Avoid the last 10 videos/music tracks


def _load_history() -> dict:
    """Loads the run history from the JSON file."""
    if not HISTORY_FILE.exists():
        return {"categories": [], "videos": [], "music": []}
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logging.warning("Could not read history file. Starting with a fresh history.")
        return {"categories": [], "videos": [], "music": []}


def _save_history(history: dict):
    """Saves the updated run history to the JSON file."""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)


def get_next_item(item_type: str, all_items: list) -> str:
    """
    Selects the next item (category, video, music) intelligently, avoiding recent repeats.

    Args:
        item_type: The type of item to select ('category', 'video', 'music').
        all_items: A list of all available items of that type.

    Returns:
        The path or name of the selected item.
    """
    if not all_items:
        raise ValueError(f"The list of all_items for type '{item_type}' is empty.")

    history = _load_history()
    history_key = f"{item_type}s"  # e.g., 'categories'
    cooldown_size = CATEGORY_COOLDOWN if item_type == 'category' else ASSET_COOLDOWN

    recent_items = history.get(history_key, [])

    # Find items that are not in the recent list
    available_items = [item for item in all_items if item not in recent_items]

    # If all items are in the cooldown period (e.g., small number of assets),
    # just pick from the full list to avoid errors.
    if not available_items:
        logging.warning(f"All {item_type} items are on cooldown. Picking from full list.")
        available_items = all_items

    # Select a random item from the available pool
    selected_item = random.choice(available_items)

    # Update the history
    recent_items.append(selected_item)
    if len(recent_items) > cooldown_size:
        history[history_key] = recent_items[-cooldown_size:]  # Keep only the most recent items
    else:
        history[history_key] = recent_items

    _save_history(history)

    logging.info(
        f"Selected {item_type}: {Path(selected_item).name if isinstance(selected_item, Path) else selected_item}")
    return selected_item

# No standalone test block needed, as this is a utility module called by main.py