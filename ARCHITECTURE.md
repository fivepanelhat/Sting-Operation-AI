# Sting-Operation-AI: Vision Architecture

This document describes the offline computer vision pipeline and dataset structures designed to detect and target invasive wasps.

---

## Model Pipeline

The sentinel box runs a customized YOLOv8 object detection model on edge hardware:

```text
  ┌─────────────┐
  │ Camera Feed ├──────► [Pre-processing (Resizing, Normalization)]
  └─────────────┘
                               │
                               ▼
  ┌─────────────┐        ┌─────────────┐
  │ Hailo-10L    │◄───────┤ YOLOv8 OBB  │
  │ Accelerator │        │ Classifier  │
  └──────┬──────┘        └─────────────┘
         │
         ▼
  ┌─────────────┐
  │ Class Label ├──────► [Actuator logic: Trigger Relay (Pin 18) if Class == 1 (Wasp)]
  └─────────────┘
```

---

## 1. Dataset Class Remapping & Integrity

### The Class Mapping Problem
In original Roboflow exports, the German Wasp (`Vespula_germanica`) was cataloged as Class `0`. However, in YOLO dataset configurations, Class `0` represents the Honeybee (`Apis_mellifera`). This overlap caused the model to classify wasps as bees and vice-versa, neutralizing the sentinel box's security guard mechanisms.

### The Fix (`tools/tidy_and_fix.py`):
This script walks through all YOLO label files (`.txt` files under `data/labels/train` and `data/labels/val`) and updates indices:
- Class `0` (Honeybees) -> Retained as Class `0` (Apis_mellifera)
- Class `0` incorrectly tagged for wasps -> Remapped to Class `1` (Vespula_germanica)

---

## 2. Oriented Bounding Boxes (OBB)

Standard axis-aligned bounding boxes (AABB) capture a significant amount of background noise when insects are oriented diagonally during flight. 
Sting-Operation-AI uses **Oriented Bounding Boxes (OBB)**:
- Label coordinates use five floats per box: `[x_center, y_center, width, height, angle_radians]`.
- This increases targeting precision and allows the servo controls to estimate the exact orientation of the insect's abdomen for actuation.

---

## 3. Edge Compilation & Quantization (Hailo-10L)

To achieve real-time latency (<15ms) on the Raspberry Pi 5, the trained PyTorch weights (`best.pt`) are compiled into a HEF (Hailo Executable Format) file:
1. **Export to ONNX:** The model is exported to an ONNX graph with static input shapes (e.g. 640x640).
2. **Quantization:** The Hailo Software Suite quantizes the model from FP32 to INT8 precision using representative validation images to minimize accuracy degradation.
3. **Compilation:** The Hailo Compiler compiles the quantized graph into a `.hef` file loaded directly into the Hailo-10L hardware buffer.
