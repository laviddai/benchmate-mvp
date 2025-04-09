import os
import yaml

def load_yaml_config(config_path):
    # Convert to absolute path relative to project root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    full_path = os.path.join(base_dir, config_path)

    with open(full_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
