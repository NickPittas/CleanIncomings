import json
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            print(f"Loaded patterns config from: {config_path}")
            return config
    except Exception as e:
        print(f"Failed to load config from {config_path}: {e}")
        print("Using fallback patterns")
        return {}

