
import sys
from ultralytics import YOLO
import os

def run_inference(image_path):
    model = YOLO('models/trained_models/sting_operation_v3/weights/best.pt')
    results = model.predict(source=image_path, conf=0.25, save=True)
    print(f'Predictions saved for {image_path}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_inference(sys.argv[1])
    else:
        print('Usage: python predict.py <path_to_image>')
