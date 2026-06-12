import os
import sys
import argparse
from ultralytics import YOLO


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


def load_env_key():
    """Attempts to read ROBOFLOW_API_KEY from environment or .env file."""
    # Try environment first
    key = os.environ.get("ROBOFLOW_API_KEY")
    if key:
        return key

    # Try local .env file
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("ROBOFLOW_API_KEY="):
                    return line.strip().split("=")[1]
    return None


def run_local_inference(
    source, model_path=None, conf=0.25, save=True, device=""
):
    """Runs inference using a local YOLO model."""
    if model_path is None:
        model_path = find_best_model()
        if model_path is None:
            print("ERROR: No trained model weights found in the repository!")
            print("Please run train.py first or specify weights using -m.")
            sys.exit(1)
        print(f"Using auto-detected local model: {model_path}")
    else:
        if not os.path.exists(model_path):
            print(f"ERROR: Specified model weights not found at: {model_path}")
            sys.exit(1)
        print(f"Using local model: {model_path}")

    model = YOLO(model_path)
    results = model.predict(source=source, conf=conf, save=save, device=device)

    print("\n=== Local YOLO Detection Summary ===")
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
                x, y, w, h = box.xywh[0].tolist()
                print(
                    f"  - Class: {cls_name} (conf: {conf_score:.2f}), BBox: [{x:.1f}, {y:.1f}, {w:.1f}, {h:.1f}]"
                )

            summary_str = ", ".join(
                [f"{count} {name}(s)" for name, count in class_counts.items()]
            )
            print(f"  Summary: Found {summary_str}")

        if save and hasattr(result, "save_dir"):
            print(f"  Saved visual result to: {result.save_dir}")


def run_roboflow_inference(source, conf=0.25, save=True):
    """Runs inference using Roboflow's hosted model API."""
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

    # Check if directory or file
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
                    print(
                        f"  - Class: {cls_name} (conf: {conf_score:.2f}), BBox Center: [{x:.1f}, {y:.1f}], Size: [{w:.1f}x{h:.1f}]"
                    )

                summary_str = ", ".join(
                    [
                        f"{count} {name}(s)"
                        for name, count in class_counts.items()
                    ]
                )
                print(f"  Summary: Found {summary_str}")

            if save:
                output_path = os.path.join(
                    "runs/detect/predict_roboflow", os.path.basename(img_path)
                )
                prediction.save(output_path)
                print(f"  Saved visual result to: {output_path}")

        except Exception as e:
            print(f"  ERROR: Failed running inference on {img_path}: {e}")


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
        help="Device to run local YOLO (e.g. cpu, cuda, or 0)",
    )
    parser.add_argument(
        "-rf",
        "--roboflow",
        action="store_true",
        help="Use Roboflow Cloud Inference API instead of local model",
    )

    args = parser.parse_args()

    # Verify source exists
    if not os.path.exists(args.source):
        print(f"ERROR: Inference source does not exist: {args.source}")
        sys.exit(1)

    if args.roboflow:
        run_roboflow_inference(
            source=args.source, conf=args.conf, save=not args.no_save
        )
    else:
        run_local_inference(
            source=args.source,
            model_path=args.model,
            conf=args.conf,
            save=not args.no_save,
            device=args.device,
        )
