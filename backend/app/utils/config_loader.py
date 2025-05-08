# backend/app/utils/config_loader.py

import yaml
from pathlib import Path

def load_yaml_config(rel_path: str) -> dict:
    """
    Load a YAML file under app/config.
    rel_path is like "benchtop/biology/omics/transcriptomics/bulk-rna-seq/volcano.yaml"
    """
    # __file__ = .../backend/app/utils/config_loader.py
    config_dir = Path(__file__).resolve().parent.parent / "config"
    full_path = config_dir / rel_path

    if not full_path.exists():
        raise RuntimeError(f"Config file not found: {full_path}")

    with full_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
