
# Sting Operation AI: Bee and Wasp Detection

## Project Goal
The primary goal of this project is to develop and enhance an object detection model capable of accurately identifying and differentiating between three key insect species: 'Apis_mellifera' (honeybees), 'Vespula_germanica' (German wasps), and 'Vespa_velutina' (Yellow-legged hornets). A particular focus is placed on improving the detection accuracy of 'Vespula_germanica' through data augmentation and model retraining.

## Directory Structure
```
Sting_Operation_AI/
├── data/
│   ├── images/  # Contains training and validation images
│   │   ├── train/
│   │   └── val/
│   ├── labels/  # Contains training and validation YOLO-format labels
│   │   ├── train/
│   │   └── val/
├── models/
│   ├── base_weights/    # Pre-trained model weights (e.g., yolov8n.pt)
│   └── trained_models/  # Saved weights and runs from training experiments
├── config/      # Configuration files, including data.yaml
├── test_inference/ # Directory for testing model inference on new media
├── .gitignore   # Specifies files and directories to ignore in version control
└── README.md    # This project documentation file
```

## Setup Instructions

### 1. Google Drive Setup
Ensure your Google Drive is mounted in Google Colab and the project directory structure, as outlined above, is created. The base path for the project is `/content/drive/MyDrive/Sting_Operation_AI`.

### 2. Install Dependencies
```bash
pip install ultralytics roboflow
```

### 3. Roboflow Data Acquisition
Utilize the Roboflow API to download the initial dataset and any additional augmented datasets. Replace the `api_key`, `workspace_name`, `project_name`, and `version` as appropriate in the provided Colab notebook cells.

### 4. Configure `data.yaml`
Verify that the `config/data.yaml` file correctly points to the dataset paths and defines the class names as:
```yaml
path: /content/drive/MyDrive/Sting_Operation_AI/data
train: images/train
val: images/val
names:
  0: Apis_mellifera
  1: Vespula_germanica
  2: Vespa_velutina
```

### 5. Model Training
Train the YOLOv8 model using the provided training script in the Colab notebook. Adjust `epochs`, `imgsz`, and `device` as needed.

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

*Note: In this iteration, the data augmentation did not significantly improve the specific mAP metrics for Vespula_germanica or the overall performance. Further efforts would focus on acquiring more diverse and quantity-rich datasets specifically targeting Vespula_germanica, increasing training epochs, or exploring advanced data augmentation techniques.*

## How to Run Inference
Load the trained `best.pt` or `last.pt` weights from the `models/trained_models/` directory and use the `model.predict()` method on new images or videos. Examples are provided in the Colab notebook.
