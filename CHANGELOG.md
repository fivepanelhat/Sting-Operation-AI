# Changelog

## [1.3.0] - 2026-07-10

### Changed
- Edge inference engine in `src/inference.py` with YOLO cache, device auto-select, wasp alert flag.
- `predict.py` reuses a warm `StingInferenceEngine`; directory inference without reloading weights.
- Hailo NPU optional (`STING_PREFER_HAILO` / `STING_HEF_PATH`) with clear fallback to YOLO.
- Flywheel JSONL rotation for SD-card safety.
- Training defaults: workers/cache/AMP tuned for lab vs CPU.
- Expanded unit tests (no GPU download required for core helpers).

### Fixed
- Import-time crash when `hailo_platform` is absent (common on dev workstations).

---
# Sting Operation AI Changelog

All notable changes to the `Sting-Operation-AI` repository will be documented in this file.

## [1.2.0] - 2026-06-08

### Added
- Created `src/inference.py` for physical/virtual Hailo NPU communication channel setup.

## [1.0.0] - 2026-06-07

### Added
- Implemented `train.py` CLI training script supporting CUDA/CPU autodetection.
- Implemented `predict.py` robust inference client supporting automatic weight discovery and optional Roboflow cloud API.
- Implemented label class validation and remapping script in `tools/tidy_and_fix.py`.
- Added dataset status checker `tools/verify_setup.py`.
- Added edge GPIO targeting documentation in `docs/HARDWARE_SETUP.md`.
- Added local Docker container deployment configurations (`Dockerfile`, `docker-compose.yml`).
- Established workspace compatibility, common license, and developer requirements.

### Fixed
- **Label Mapping Bug:** Fixed class mappings where Roboflow exported German wasps (`Vespula germanica`) as Class 0 (bees). Remapped German wasps to Class 1, and honeybees to Class 0 to prevent model classification confusion.
- Organized dataset assets (moved raw labels to `data/raw_annotations/`, screenshots to `data/visualizations/`).
