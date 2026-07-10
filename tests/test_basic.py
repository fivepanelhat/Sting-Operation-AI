"""Lightweight unit tests — no GPU / model download required."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.model_paths import (  # noqa: E402
    DEFAULT_NAMES,
    auto_device,
    find_best_model,
    is_wasp_class,
    load_class_names,
)
from src.flywheel_util import rotate_flywheel_if_needed  # noqa: E402
from src.inference import Detection, InferenceResult, StingInferenceEngine  # noqa: E402


def test_dummy():
    assert True


def test_load_class_names_from_config():
    names = load_class_names(ROOT / "config" / "data.yaml")
    assert names[0] == "Apis_mellifera"
    assert names[1] == "Vespula_germanica"
    assert names[2] == "Vespa_velutina"


def test_load_class_names_missing_file_fallback(tmp_path):
    names = load_class_names(tmp_path / "missing.yaml")
    assert names == DEFAULT_NAMES


def test_is_wasp_class():
    assert is_wasp_class("Vespula_germanica") is True
    assert is_wasp_class("Vespa_velutina") is True
    assert is_wasp_class("Apis_mellifera") is False
    assert is_wasp_class("honeybee") is False


def test_auto_device_explicit():
    assert auto_device("cpu") == "cpu"


def test_find_best_model_env(tmp_path, monkeypatch):
    fake = tmp_path / "fake.pt"
    fake.write_bytes(b"not-a-real-model")
    monkeypatch.setenv("STING_MODEL_PATH", str(fake))
    assert find_best_model() == str(fake)


def test_rotate_flywheel(tmp_path):
    p = tmp_path / "flywheel.jsonl"
    lines = [f'{{"i": {i}, "x": "{"y" * 100}"}}' for i in range(50)]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert p.stat().st_size > 200
    rotated = rotate_flywheel_if_needed(p, max_bytes=200, keep_lines=5)
    assert rotated is True
    kept = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(kept) == 5


def test_inference_result_counts_and_alert():
    dets = [
        Detection(0, "Apis_mellifera", 0.9, is_wasp=False),
        Detection(1, "Vespula_germanica", 0.8, is_wasp=True),
        Detection(1, "Vespula_germanica", 0.7, is_wasp=True),
    ]
    r = InferenceResult(
        source="x.jpg",
        detections=dets,
        latency_seconds=0.01,
        backend="yolo",
        wasp_alert=True,
    )
    assert r.counts["Apis_mellifera"] == 1
    assert r.counts["Vespula_germanica"] == 2
    assert r.wasp_alert is True


def test_engine_requires_model_when_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("STING_MODEL_PATH", raising=False)
    monkeypatch.delenv("STING_PREFER_HAILO", raising=False)
    # Point candidates at empty dir by patching find
    monkeypatch.setattr(
        "src.inference.find_best_model",
        lambda *a, **k: None,
    )
    with pytest.raises(FileNotFoundError):
        StingInferenceEngine(model_path=None, prefer_hailo=False)


def test_predict_module_exports():
    import predict

    assert hasattr(predict, "run_local_inference")
    assert hasattr(predict, "find_best_model")
