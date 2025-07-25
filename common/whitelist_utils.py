import json
import os

WHITELIST_PATH = "whitelist.json"

def load_whitelist() -> dict[int, dict]:
    if not os.path.isfile(WHITELIST_PATH):
        return {}
    with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
        except json.JSONDecodeError:
            return {}

def save_whitelist(whitelist: dict[int, dict]):
    with open(WHITELIST_PATH, "w", encoding="utf-8") as f:
        json.dump(whitelist, f, ensure_ascii=False, indent=2)