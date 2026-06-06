
from ultralytics import YOLO
import sys

def main():
    model = YOLO('yolov8n.pt')
    model.train(
        data='config/data.yaml',
        epochs=50,
        imgsz=640,
        project='models/trained_models',
        name='v4_final_run'
    )

if __name__ == '__main__':
    main()
