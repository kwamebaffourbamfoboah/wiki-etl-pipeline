import json
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config():
    """Read config.json from the same folder as this file."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)