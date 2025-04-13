# backend/app/utils/config-loader.py

import os
import yaml

def load_yaml_config(config_path):
    """
    Load a YAML configuration file, given its path relative to the project root.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    full_path = os.path.join(base_dir, config_path)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Error loading config from {full_path}: {e}")
