# Sting Operation AI Changelog

All notable changes to the `Sting-Operation-AI` repository will be documented in this file.

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
