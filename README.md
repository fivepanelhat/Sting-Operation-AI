# Sting Operation AI: Bee and Wasp Detection

## Project Goal
The primary goal of this project is to develop and enhance an object detection model capable of accurately identifying and differentiating between three key insect species:
- `Apis_mellifera` (honeybees - Class 0)
- `Vespula_germanica` (German wasps - Class 1)
- `Vespa_velutina` (Yellow-legged hornets - Class 2)

A particular focus is placed on improving the detection accuracy of `Vespula_germanica` through targeted data acquisition, augmentation, and model retraining.

---

## Directory Structure
```
Sting_Operation_AI/
├── .venv/               # Local Python virtual environment
├── config/              # Configuration files
│   └── data.yaml        # Dataset configuration (mapped class names and relative paths)
├── data/
│   ├── images/          # Training and validation images
│   │   ├── train/       # 8 training images
│   │   └── val/         # 4 validation images
│   ├── labels/          # YOLO-format annotation labels (Class 1 for Vespula_germanica)
│   │   ├── train/       # Training labels
│   │   └── val/         # Validation labels
│   ├── raw_annotations/ # Raw pixel-coordinate Oriented Bounding Box (OBB) annotations
│   └── visualizations/  # Roboflow annotation visual validation screenshots
├── models/
│   ├── base_weights/    # Pre-trained base models (e.g., yolov8n.pt)
│   └── trained_models/  # Experiment runs and trained model weights (v1, v2, v3, etc.)
├── tools/               # Auxiliary scripts for setup, repair, and verification
│   ├── tidy_and_fix.py  # Repository cleanup and label class correction script
│   └── verify_setup.py  # Automated environment and dataset integrity check
├── .gitignore           # Git ignore configurations (filters out cache, weights, and venv)
├── predict.py           # Robust inference runner script
├── train.py             # Advanced CLI-based model training script
├── setup_project.bat    # Windows batch script for automated local setup
└── README.md            # Project documentation (this file)
```

---

## Setup Instructions

### 1. Local Automated Setup (Windows)
We provide an automated setup batch script that creates the virtual environment, installs dependencies, fixes label mappings, cleans up directories, and verifies the environment.
Double-click `setup_project.bat` or run:
```cmd
setup_project.bat
```

### 2. Manual Setup
If you prefer setting up manually or are on another operating system:

**Create Virtual Environment and Install Dependencies:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt  # Or: pip install ultralytics pyyaml
```

**Clean and Fix Dataset:**
```bash
python tools/tidy_and_fix.py
```

**Verify Setup:**
```bash
python tools/verify_setup.py
```

---

## Dataset & Label Corrections

### Bug Fix: Wasp Class Mapping
Previously, Roboflow-exported labels mapped German Wasps (`Vespula_germanica`) to class index `0`. However, in `config/data.yaml`, class `0` is defined as `Apis_mellifera` (honeybees), causing the model to learn incorrect classifications. 

The `tools/tidy_and_fix.py` script automatically scans all dataset labels and maps German Wasps to class index `1` (`Vespula_germanica`).

### Reorganization
- **Misplaced text annotations**: Raw pixel-coordinate OBB files from Roboflow are moved from `data/images/train/` to `data/raw_annotations/`.
- **Annotation screenshots**: Screenshots showing bounding boxes from the exporter are moved from `data/labels/` to `data/visualizations/`.
- **Cache files**: YOLO data loader cache files (`.cache`) are untracked and excluded via `.gitignore`.

---

## How to Run Inference

Use the enhanced `predict.py` script. It automatically detects the best trained weights in your repository (falling back from `v3` to `v2`, `v1`, or a base model if needed):

```bash
# Run inference on a validation image
python predict.py data/images/val/985d1c64-8272-47e7-9fd2-1b7a2399a189_jpg.rf.6e92e8483f9bd8f94270a7256149f481.jpg

# Specify a custom model and confidence threshold
python predict.py data/images/val/ -m models/trained_models/sting_operation_v3/weights/best.pt -c 0.3
```

---

## How to Train

The training script supports command-line configuration and automatically handles hardware detection (GPU/CUDA or CPU):

```bash
# Train with default parameters (50 epochs, yolov8n.pt base model)
python train.py

# Custom training configuration
python train.py --epochs 100 --imgsz 640 --name v4_final_run --device cuda
```

---

## Model Performance Summary

### Initial Model Performance (before data augmentation)
- **Overall mAP50**: 0.2263
- **Overall mAP50-95**: 0.0919
- **mAP50 for Vespula_germanica**: 0.0681
- **mAP50-95 for Vespula_germanica**: 0.0343

### Augmented Model Performance (after data augmentation)
- **Overall mAP50**: 0.2263
- **Overall mAP50-95**: 0.0919
- **mAP50 for Vespula_germanica**: 0.0681
- **mAP50-95 for Vespula_germanica**: 0.0343

*Note: In this iteration, the data augmentation did not significantly improve the specific mAP metrics for Vespula_germanica or the overall performance. Correcting the wasp labels from class 0 to class 1 is expected to resolve the low class-specific performance.*
