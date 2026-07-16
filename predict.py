"""
Sting Operation AI - Predict with Full Data Flywheel Integration

Edge-optimised local YOLO path (model cache, device auto-select, flywheel rotation).
Optional Roboflow cloud path remains available for lab use only.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

# Ensure repo root / src importable when run as script
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
 sys.path.insert(0, str(_ROOT))

from src.flywheel_util import rotate_flywheel_if_needed # noqa: E402
from src.inference import StingInferenceEngine # noqa: E402
from src.model_paths import find_best_model as find_best_model # re-export for CLI/tools # noqa: E402

# Re-export for callers/tests
__all_reexport = find_best_model

# Module-level engine cache (warm weights across repeated CLI use in process)
_ENGINE: StingInferenceEngine | None = None


def get_engine(
 model_path: str | None = None,
 conf: float = 0.25,
 device: str = "",
 imgsz: int = 640,
) -> StingInferenceEngine:
 global _ENGINE
 if (
 _ENGINE is None
 or (model_path and model_path != _ENGINE.model_path)
 or conf != _ENGINE.conf
 or (device and device != _ENGINE.device)
 or imgsz != _ENGINE.imgsz
 ):
 _ENGINE = StingInferenceEngine(
 model_path=model_path,
 conf=conf,
 device=device,
 imgsz=imgsz,
 )
 return _ENGINE


def run_local_inference(
 source,
 model_path=None,
 conf=0.25,
 save=True,
 device="",
 imgsz=640,
):
 """Runs inference using a local YOLO model with flywheel + telemetry."""
 try:
 from coastal_alpine_core.telemetry import TelemetryTracker
 from coastal_alpine_core import DataFlywheel, Trajectory

 has_core = True
 except ImportError:
 has_core = False
 TelemetryTracker = None # type: ignore

 engine = get_engine(
 model_path=model_path, conf=conf, device=device, imgsz=imgsz
 )
 print(f"Using model: {engine.model_path} (device={engine.device}, backend={engine.backend})")

 measurement = None
 if has_core:
 measurement = TelemetryTracker.measure_latency("sting_local_inference")

 t0 = time.perf_counter()
 # Directory: one engine, many files (reuse weights)
 source_path = Path(source)
 if source_path.is_dir():
 images = sorted(
 p
 for p in source_path.iterdir()
 if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
 )
 if not images:
 print("No processable images found in directory.")
 return []
 results = engine.predict_many(images, conf=conf, save=save)
 else:
 results = [engine.predict(source, conf=conf, save=save)]

 # Flywheel (per-result + rotation)
 if has_core:
 try:
 flywheel = DataFlywheel(storage_path=engine.flywheel_path)
 for result in results:
 total = len(result.detections)
 avg_conf = (
 sum(d.confidence for d in result.detections) / total
 if total
 else 0.0
 )
 traj = Trajectory(
 trajectory_id=str(uuid.uuid4()),
 timestamp=datetime.now().isoformat(),
 action="local_yolo_inference",
 input_summary=f"Source: {result.source}",
 output_summary=(
 f"Detections: {total}, Avg Conf: {avg_conf:.2f}, "
 f"WaspAlert: {result.wasp_alert}"
 ),
 outcome=(
 "wasp_alert"
 if result.wasp_alert
 else ("success" if total > 0 else "no_detection")
 ),
 latency_seconds=result.latency_seconds,
 estimated_energy_joules=0.0,
 metadata={
 "model_path": result.model_path,
 "backend": result.backend,
 "total_detections": total,
 "avg_confidence": round(avg_conf, 3),
 "counts": result.counts,
 "wasp_alert": result.wasp_alert,
 "source": str(result.source),
 },
 )
 flywheel.record_trajectory(traj)
 rotate_flywheel_if_needed(engine.flywheel_path)
 except Exception as e:
 print(f"Warning: Flywheel recording failed: {e}")

 TelemetryTracker.complete_measurement(
 measurement, include_system_metrics=True
 )
 else:
 elapsed = time.perf_counter() - t0
 print(f"Inference batch completed in {elapsed:.3f}s (core SDK not installed)")

 print("\n=== Local YOLO Detection Summary ===")
 for result in results:
 base = os.path.basename(str(result.source))
 if not result.detections:
 print(f"{base}: no objects detected ({result.latency_seconds*1000:.1f} ms)")
 continue
 summary = ", ".join(
 f"{count} {name}(s)" for name, count in result.counts.items()
 )
 alert = " [WASP ALERT]" if result.wasp_alert else ""
 print(
 f"{base}: {summary} "
 f"({result.latency_seconds*1000:.1f} ms){alert}"
 )

 return results


def load_env_key():
 """Attempts to read ROBOFLOW_API_KEY from environment or .env file."""
 key = os.environ.get("ROBOFLOW_API_KEY")
 if key:
 return key

 env_path = ".env"
 if os.path.exists(env_path):
 with open(env_path, "r", encoding="utf-8") as f:
 for line in f:
 if line.startswith("ROBOFLOW_API_KEY="):
 return line.strip().split("=", 1)[1]
 return None


def run_roboflow_inference(source, conf=0.25, save=True):
 """Runs inference using Roboflow's hosted model API (lab only - not edge)."""
 print("Initializing Roboflow Hosted API Client...")
 try:
 from roboflow import Roboflow
 except ImportError:
 print(
 "ERROR: Roboflow SDK not installed! Run `pip install roboflow` first."
 )
 sys.exit(1)

 api_key = load_env_key()
 if not api_key:
 import getpass

 api_key = getpass.getpass(
 "Please enter your Roboflow Private API Key: "
 ).strip()
 if not api_key:
 print("ERROR: Roboflow API key is required for cloud inference.")
 sys.exit(1)

 try:
 rf = Roboflow(api_key=api_key)
 project = rf.workspace("ws-workspace-yhner").project(
 "example-ueewe-bw1lr"
 )
 model = project.version(1).model
 except Exception as e:
 print(f"ERROR: Failed to initialize Roboflow model: {e}")
 sys.exit(1)

 images_to_process = []
 if os.path.isdir(source):
 for file in os.listdir(source):
 if file.lower().endswith((".png", ".jpg", ".jpeg")):
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
 prediction = model.predict(img_path, confidence=int(conf * 100))
 pred_json = prediction.json()
 predictions = pred_json.get("predictions", [])

 if not predictions:
 print(" No objects detected.")
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
 print(
 f" - Class: {cls_name} (conf: {conf_score:.2f}), "
 f"BBox Center: [{x:.1f}, {y:.1f}], Size: [{w:.1f}x{h:.1f}]"
 )

 summary_str = ", ".join(
 f"{count} {name}(s)" for name, count in class_counts.items()
 )
 print(f" Summary: Found {summary_str}")

 if save:
 output_path = os.path.join(
 "runs/detect/predict_roboflow", os.path.basename(img_path)
 )
 prediction.save(output_path)
 print(f" Saved visual result to: {output_path}")

 except Exception as e:
 print(f" ERROR: Failed running inference on {img_path}: {e}")


if __name__ == "__main__":
 parser = argparse.ArgumentParser(
 description="Sting Operation AI - Inference Script"
 )
 parser.add_argument(
 "source", type=str, help="Path to image, directory, or video source"
 )
 parser.add_argument(
 "-m",
 "--model",
 type=str,
 default=None,
 help="Path to YOLO model weights (.pt)",
 )
 parser.add_argument(
 "-c",
 "--conf",
 type=float,
 default=0.25,
 help="Confidence threshold (default: 0.25)",
 )
 parser.add_argument(
 "--no-save",
 action="store_true",
 help="Do not save visual prediction results",
 )
 parser.add_argument(
 "-d",
 "--device",
 type=str,
 default="",
 help="Device for local YOLO (cpu, cuda, or 0). Default: auto",
 )
 parser.add_argument(
 "--imgsz",
 type=int,
 default=int(os.getenv("STING_IMGSZ", "640")),
 help="Inference image size (default: 640; lower = faster on Pi CPU)",
 )
 parser.add_argument(
 "-rf",
 "--roboflow",
 action="store_true",
 help="Use Roboflow Cloud Inference API instead of local model",
 )
 args = parser.parse_args()

 if not os.path.exists(args.source):
 print(f"ERROR: Inference source does not exist: {args.source}")
 sys.exit(1)

 if args.roboflow:
 run_roboflow_inference(args.source, args.conf, not args.no_save)
 else:
 run_local_inference(
 args.source,
 args.model,
 args.conf,
 not args.no_save,
 args.device,
 args.imgsz,
 )
