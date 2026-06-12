import os
import sys
import argparse
import yaml
from ultralytics import YOLO


def check_data_config(data_cfg_path):
    """Verifies that the data config exists and has valid paths."""
    if not os.path.exists(data_cfg_path):
        print(f"ERROR: Dataset config file not found at: {data_cfg_path}")
        return False

    try:
        with open(data_cfg_path, "r") as f:
            cfg = yaml.safe_load(f)

        data_path = cfg.get("path", "")
        # If relative path, resolve relative to config directory or current working directory
        resolved_path = (
            data_path
            if os.path.isabs(data_path)
            else os.path.abspath(data_path)
        )

        train_path = os.path.join(resolved_path, cfg.get("train", ""))
        val_path = os.path.join(resolved_path, cfg.get("val", ""))

        print("Resolving paths from dataset config:")
        print(f"  Dataset base directory: {resolved_path}")
        print(f"  Training images folder: {train_path}")
        print(f"  Validation images folder: {val_path}")

        if not os.path.exists(resolved_path):
            print(
                f"ERROR: Dataset base directory does not exist: {resolved_path}"
            )
            return False

        if not os.path.exists(train_path):
            print(f"ERROR: Training directory does not exist: {train_path}")
            return False

        if not os.path.exists(val_path):
            print(f"ERROR: Validation directory does not exist: {val_path}")
            return False

        print("Dataset config paths validated successfully.")
        return True

    except Exception as e:
        print(f"ERROR: Failed to validate dataset config: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Sting Operation AI - Training Script"
    )
    parser.add_argument(
        "-d",
        "--data",
        type=str,
        default="config/data.yaml",
        help="Path to data.yaml config (default: config/data.yaml)",
    )
    parser.add_argument(
        "-e",
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs (default: 50)",
    )
    parser.add_argument(
        "-i",
        "--imgsz",
        type=int,
        default=640,
        help="Image size (default: 640)",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Base model weights (default: yolov8n.pt)",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="v4_final_run",
        help="Experiment name (default: v4_final_run)",
    )
    parser.add_argument(
        "-p",
        "--project",
        type=str,
        default="models/trained_models",
        help="Project save directory (default: models/trained_models)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Device to run on (e.g. cpu, cuda, or 0)",
    )

    args = parser.parse_args()

    # 1. Validate dataset config
    if not check_data_config(args.data):
        sys.exit(1)

    # 2. Determine device
    device = args.device
    if not device:
        # Check if CUDA is available via torch
        try:
            import torch

            if torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        except ImportError:
            device = "cpu"

    print("\nTraining configuration:")
    print(f"  Base Model:   {args.model}")
    print(f"  Data Config:  {args.data}")
    print(f"  Epochs:       {args.epochs}")
    print(f"  Image Size:   {args.imgsz}")
    print(f"  Save Project: {args.project}")
    print(f"  Run Name:     {args.name}")
    print(f"  Device:       {device.upper()}")
    print("Starting training...")

    # 3. Load and train model
    try:
        model = YOLO(args.model)
        model.train(
            data=args.data,
            epochs=args.epochs,
            imgsz=args.imgsz,
            project=args.project,
            name=args.name,
            device=device,
        )
        print(
            f"\nTraining completed successfully! Results saved under {os.path.join(args.project, args.name)}"
        )
    except Exception as e:
        print(f"\nERROR: Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
