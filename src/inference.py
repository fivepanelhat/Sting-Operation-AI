import os
from hailo_platform import VDevice

# Point directly to your persistent data partition path
MODEL_PATH = "/mnt/sovereign-data/models/sting_vision_v5.hef"


def init_npu():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Sovereign model file missing from storage array: {MODEL_PATH}"
        )

    # The Hailo NPU virtual device creates its internal allocations inside /dev/hailo0
    # Because /dev is a virtual filesystem (devtmpfs), it remains read-write in RAM naturally.
    target_vdevice = VDevice()
    print("[MINT] Hailo-10H NPU communication channel initialized safely.")
    return target_vdevice
