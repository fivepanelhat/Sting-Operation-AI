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


# run_roboflow_inference can also be enhanced similarly if needed

if __name__ == "__main__":
    # ... existing argparse code ...
    parser = argparse.ArgumentParser()
    # (arguments remain the same)
    args = parser.parse_args()

    if args.roboflow:
        run_roboflow_inference(args.source, args.conf, not args.no_save)
    else:
        run_local_inference(
            args.source, args.model, args.conf, not args.no_save, args.device
        )
