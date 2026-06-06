import os
import sys
import argparse
from ultralytics import YOLO

def find_best_model():
    """Finds the best available model in the repository."""
    # List of candidate models in order of preference
    candidates = [
        'models/trained_models/sting_operation_v3/weights/best.pt',
        'models/trained_models/sting_operation_v2/weights/best.pt',
        'models/trained_models/sting_operation_v1-2/weights/best.pt',
        'models/trained_models/sting_operation_v1/weights/best.pt',
        'yolov8n.pt'
    ]
    
    for path in candidates:
        if os.path.exists(path):
            return path
            
    return None

def run_inference(source, model_path=None, conf=0.25, save=True, device=''):
    # Determine model path
    if model_path is None:
        model_path = find_best_model()
        if model_path is None:
            print("ERROR: No trained model weights found in the repository!")
            print("Please run train.py first or ensure model weights are located in models/trained_models/.")
            sys.exit(1)
        print(f"Using auto-detected model: {model_path}")
    else:
        if not os.path.exists(model_path):
            print(f"ERROR: Specified model weights not found at: {model_path}")
            sys.exit(1)
        print(f"Using model: {model_path}")

    # Load model
    model = YOLO(model_path)
    
    # Run inference
    results = model.predict(source=source, conf=conf, save=save, device=device)
    
    print("\n=== Detection Summary ===")
    for result in results:
        path = result.path
        boxes = result.boxes
        print(f"\nImage: {os.path.basename(path)}")
        if len(boxes) == 0:
            print("  No objects detected.")
        else:
            class_counts = {}
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                conf_score = float(box.conf[0])
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                
                # Print individual box details
                x, y, w, h = box.xywh[0].tolist()
                print(f"  - Class: {cls_name} (conf: {conf_score:.2f}), BBox: [{x:.1f}, {y:.1f}, {w:.1f}, {h:.1f}]")
            
            # Print count summary
            summary_str = ", ".join([f"{count} {name}(s)" for name, count in class_counts.items()])
            print(f"  Summary: Found {summary_str}")
            
        if save and hasattr(result, 'save_dir'):
            print(f"  Saved result to: {result.save_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sting Operation AI - Inference Script")
    parser.add_argument("source", type=str, help="Path to image, directory, or video source")
    parser.add_argument("-m", "--model", type=str, default=None, help="Path to YOLO model weights (.pt)")
    parser.add_argument("-c", "--conf", type=float, default=0.25, help="Confidence threshold (default: 0.25)")
    parser.add_argument("--no-save", action="store_true", help="Do not save visual prediction results")
    parser.add_argument("-d", "--device", type=str, default="", help="Device to run inference on (e.g. cpu, cuda, or 0)")
    
    args = parser.parse_args()
    
    # Verify source exists
    if not os.path.exists(args.source):
        print(f"ERROR: Inference source does not exist: {args.source}")
        sys.exit(1)
        
    run_inference(
        source=args.source,
        model_path=args.model,
        conf=args.conf,
        save=not args.no_save,
        device=args.device
    )
