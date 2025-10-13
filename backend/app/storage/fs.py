"""File storage utilities"""
import os
from pathlib import Path

def ensure_dir(path: str):
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)

def save_artifact(data: bytes, filename: str, artifact_dir: str = "./artifacts"):
    """Save model artifact to filesystem"""
    ensure_dir(artifact_dir)
    filepath = os.path.join(artifact_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(data)
    return filepath
