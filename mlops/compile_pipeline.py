import os
import sys

try:
    from hailo_sdk_client import ClientRunner
except ImportError:
    print(
        "[ERROR] Hailo Software Suite Compiler Toolchain not detected locally."
    )
    sys.exit(1)


def run_quantization_pipeline(
    onnx_model_path, calibration_data_dir, output_hef_name
):
    """
    Automates the local translation, optimization, and INT8 quantization of raw
    AI models directly for the physical Hailo-10H NPU architecture.
    """
    print(f"[MLOPS] Commencing compilation of model target: {onnx_model_path}")

    # 1. Initialize the compilation runner
    runner = ClientRunner()

    # 2. Parse the network layout from ONNX translation boundary
    model_name = os.path.basename(onnx_model_path).split(".")[0]
    runner.translate_onnx_model(onnx_model_path, model_name)
    print(
        "[SUCCESS] Model topology verified and parsed into local graph structures."
    )

    # 3. Apply the Optimization and Calibration Profile
    # This executes the step down to INT8 configuration matrix metrics
    alls_script = """
    normalization1 = normalization([0.0, 0.0, 0.0], [255.0, 255.0, 255.0])
    model_optimization_config(precision=int8)
    """
    runner.load_model_script(alls_script)

    # 4. Execute the Quantization using your local site image sets
    # This prevents the AI model from losing precision out in the Taranaki landscape context
    print(
        "[OPTIMIZING] Injecting calibration dataset into compression layer..."
    )
    runner.optimize_full(calibration_data_dir)

    # 5. Compile into the final physical binary artifact
    output_path = f"/mnt/sovereign-data/models/{output_hef_name}.hef"
    print(
        f"[COMPILING] Forging final HEF engine payload to target: {output_path}"
    )

    runner.compile(output_path)
    print("[MINT] Automated MLOps loop finished. Model registry updated.")


if __name__ == "__main__":
    run_quantization_pipeline(
        "./models/raw_sting_vision.onnx",
        "./data/calibration_samples/",
        "sting_vision_v6_int8",
    )
