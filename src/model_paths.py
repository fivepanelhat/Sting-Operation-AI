"""Model discovery and class-name helpers for edge inference."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Prefer newest trained weights; fall back to nano base for CI/dev.
DEFAULT_CANDIDATES: List[str] = [
    "models/trained_models/sting_operation_v3/weights/best.pt",
    "models/trained_models/sting_operation_v2/weights/best.pt",
    "models/trained_models/sting_operation_v1-2/weights/best.pt",
    "models/trained_models/sting_operation_v1/weights/best.pt",
    "yolov8n.pt",
]

DEFAULT_NAMES = {
    0: "Apis_mellifera",
    1: "Vespula_germanica",
    2: "Vespa_velutina",
}

WASP_CLASS_NAMES = frozenset(
    {
        "Vespula_germanica",
        "Vespa_velutina",
        "wasp",
        "hornet",
        "vespula",
        "vespa",
    }
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_best_model(
    candidates: Optional[List[str]] = None,
    env_key: str = "STING_MODEL_PATH",
) -> Optional[str]:
    """Return first existing model path (absolute if under repo)."""
    env_path = os.environ.get(env_key)
    if env_path and os.path.exists(env_path):
        return env_path

    root = repo_root()
    for path in candidates or DEFAULT_CANDIDATES:
        p = Path(path)
        if not p.is_absolute():
            p = root / p
        if p.is_file():
            return str(p)
    return None


def load_class_names(data_yaml: str | Path = "config/data.yaml") -> Dict[int, str]:
    """Load YOLO class id → name mapping from data.yaml."""
    path = Path(data_yaml)
    if not path.is_absolute():
        path = repo_root() / path
    if not path.is_file():
        return dict(DEFAULT_NAMES)
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        names = cfg.get("names") or {}
        if isinstance(names, dict):
            return {int(k): str(v) for k, v in names.items()}
        if isinstance(names, list):
            return {i: str(n) for i, n in enumerate(names)}
    except (OSError, ValueError, TypeError, yaml.YAMLError):
        pass
    return dict(DEFAULT_NAMES)


def is_wasp_class(name: str) -> bool:
    n = (name or "").lower()
    if n in {w.lower() for w in WASP_CLASS_NAMES}:
        return True
    return any(k in n for k in ("wasp", "vespula", "vespa", "hornet"))


def auto_device(preferred: str = "") -> str:
    """Pick inference device: explicit preferred, else CUDA, else CPU."""
    if preferred:
        return preferred
    env = os.environ.get("STING_DEVICE", "").strip()
    if env:
        return env
    try:
        import torch

        if torch.cuda.is_available():
            return "0"
    except ImportError:
        pass
    return "cpu"
