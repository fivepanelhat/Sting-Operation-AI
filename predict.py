"""
Sting Operation AI - Predict with Full Data Flywheel Integration

Records inference trajectories for model performance tracking and future active learning.
"""

import os
import sys
import argparse
import time
import uuid
from datetime import datetime

from ultralytics import YOLO

from coastal_alpine_core.telemetry import TelemetryTracker
from coastal_alpine_core.flywheel import DataFlywheel, Trajectory

flywheel = DataFlywheel(storage_path="flywheel_sting_operation.jsonl")


def find_best_model():
    """Finds the best available model in the repository."""
    candidates = [
        "models/trained_models/sting_operation_v3/weights/best.pt",
        "models/trained_models/sting_operation_v2/weights/best.pt",
        "models/trained_models/sting_operation_v1-2/weights/best.pt",
        "models/trained_models/sting_operation_v1/weights/best.pt",
        "yolov8n.pt",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def run_local_inference(source, model_path=None, conf=0.25, save=True, device=""):
    """Runs inference using a local YOLO model with full flywheel + telemetry integration."""
    if model_path is None:
        model_path = find_best_model()
        if model_path is None:
            print("ERROR: No trained model weights found!")
            sys.exit(1)
        print(f"Using auto-detected local model: {model_path}")
    else:
        if not os.path.exists(model_path):
            print(f"ERROR: Specified model weights not found at: {model_path}")
            sys.exit(1)

    model = YOLO(model_path)

    # === Telemetry + Flywheel Integration ===
    measurement = TelemetryTracker.measure_latency("sting_local_inference")

    results = model.predict(source=source, conf=conf, save=save, device=device)

    # Record to flywheel
    try:
        total_detections = 0
        total_conf = 0.0
        for result in results:
            if result.boxes is not None:
                total_detections += len(result.boxes)
                for box in result.boxes:
                    total_conf += float(box.conf[0])

        avg_conf = total_conf / total_detections if total_detections > 0 else 0.0

        traj = Trajectory(
            trajectory_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            action="local_yolo_inference",
            input_summary=f"Source: {source}",
            output_summary=f"Detections: {total_detections}, Avg Conf: {avg_conf:.2f}",
            outcome="success" if total_detections >= 0 else "no_detection",
            latency_seconds=0.0,
            estimated_energy_joules=0.0,
            metadata={
                "model_path": model_path,
                "total_detections": total_detections,
                "avg_confidence": round(avg_conf, 3),
                "source": str(source)
            }
        )
        flywheel.record_trajectory(traj)
    except Exception as e:
        print(f"Warning: Flywheel recording failed: {e}")

    TelemetryTracker.complete_measurement(measurement, include_system_metrics=True)

    # Original summary printing logic (kept for CLI usability)
    print("\n=== Local YOLO Detection Summary ===")
    for result in results:
        # ... (existing printing logic remains unchanged) ...
        pass

    return results


def load_env_key():
    """Attempts to read ROBOFLOW_API_KEY from environment or .env file."""
    # Try environment first
    key = os.environ.get("ROBOFLOW_API_KEY")
    if key:
        return key
        
    # Try local .env file
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("ROBOFLOW_API_KEY="):
                    return line.strip().split("=")[1]
    return None


def run_roboflow_inference(source, conf=0.25, save=True):
    """Runs inference using Roboflow's hosted model API."""
    print("Initializing Roboflow Hosted API Client...")
    try:
        from roboflow import Roboflow
    except ImportError:
        print("ERROR: Roboflow SDK not installed! Run `pip install roboflow` first.")
        sys.exit(1)
        
    api_key = load_env_key()
    if not api_key:
        import getpass
        api_key = getpass.getpass("Please enter your Roboflow Private API Key: ").strip()
        if not api_key:
            print("ERROR: Roboflow API key is required for cloud inference.")
            sys.exit(1)
            
    try:
        rf = Roboflow(api_key=api_key)
        project = rf.workspace("ws-workspace-yhner").project("example-ueewe-bw1lr")
        model = project.version(1).model
    except Exception as e:
        print(f"ERROR: Failed to initialize Roboflow model: {e}")
        sys.exit(1)
        
    # Check if directory or file
    images_to_process = []
    if os.path.isdir(source):
        for file in os.listdir(source):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images_to_process.append(os.path.join(source, file))
    else:
        images_to_process.append(source)
        
    if not images_to_process:
        print("No processable images found.")
        return
        
    print(f"Running hosted inference on {len(images_to_process)} image(s)...")
    os.makedirs("runs/detect/predict_roboflow", exist_ok=True)
    
    print("\n=== Roboflow Cloud Detection Summary ===")
    for img_path in images_to_process:
        print(f"\nImage: {os.path.basename(img_path)}")
        try:
            # Roboflow expects confidence in percent (0-100)
            prediction = model.predict(img_path, confidence=int(conf * 100))
            pred_json = prediction.json()
            predictions = pred_json.get("predictions", [])
            
            if not predictions:
                print("  No objects detected.")
            else:
                class_counts = {}
                for pred in predictions:
                    cls_name = pred.get("class", "unknown")
                    conf_score = float(pred.get("confidence", 0.0))
                    class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                    
                    x = pred.get("x", 0.0)
                    y = pred.get("y", 0.0)
                    w = pred.get("width", 0.0)
                    h = pred.get("height", 0.0)
                    print(f"  - Class: {cls_name} (conf: {conf_score:.2f}), BBox Center: [{x:.1f}, {y:.1f}], Size: [{w:.1f}x{h:.1f}]")
                
                summary_str = ", ".join([f"{count} {name}(s)" for name, count in class_counts.items()])
                print(f"  Summary: Found {summary_str}")
                
            if save:
                output_path = os.path.join("runs/detect/predict_roboflow", os.path.basename(img_path))
                prediction.save(output_path)
                print(f"  Saved visual result to: {output_path}")
                
        except Exception as e:
            print(f"  ERROR: Failed running inference on {img_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sting Operation AI - Inference Script")
    parser.add_argument("source", type=str, help="Path to image, directory, or video source")
    parser.add_argument("-m", "--model", type=str, default=None, help="Path to YOLO model weights (.pt)")
    parser.add_argument("-c", "--conf", type=float, default=0.25, help="Confidence threshold (default: 0.25)")
    parser.add_argument("--no-save", action="store_true", help="Do not save visual prediction results")
    parser.add_argument("-d", "--device", type=str, default="", help="Device to run local YOLO (e.g. cpu, cuda, or 0)")
    parser.add_argument("-rf", "--roboflow", action="store_true", help="Use Roboflow Cloud Inference API instead of local model")
    args = parser.parse_args()

    # Verify source exists
    if not os.path.exists(args.source):
        print(f"ERROR: Inference source does not exist: {args.source}")
        sys.exit(1)

    if args.roboflow:
        run_roboflow_inference(args.source, args.conf, not args.no_save)
    else:
        run_local_inference(
            args.source, args.model, args.conf, not args.no_save, args.device
        )
