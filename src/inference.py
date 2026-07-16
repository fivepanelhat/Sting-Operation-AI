"""
Sting Operation edge inference engine.

Supports:
- Local Ultralytics YOLO (.pt) - default path for dev/CI and Pi without HEF
- Optional Hailo-10H HEF via hailo_platform when available

Designed for Raspberry Pi 5 16GB + Hailo-10H without requiring Hailo at import time.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from .flywheel_util import rotate_flywheel_if_needed
from .model_paths import (
 auto_device,
 find_best_model,
 is_wasp_class,
 load_class_names,
)

logger = logging.getLogger("sting.inference")

# Default HEF on sovereign storage partition (production edge)
DEFAULT_HEF_PATH = os.getenv(
 "STING_HEF_PATH", "/mnt/sovereign-data/models/sting_vision_v5.hef"
)


@dataclass
class Detection:
 class_id: int
 class_name: str
 confidence: float
 # xyxy pixel coords when available
 bbox: Optional[List[float]] = None
 is_wasp: bool = False


@dataclass
class InferenceResult:
 source: str
 detections: List[Detection] = field(default_factory=list)
 latency_seconds: float = 0.0
 backend: str = "unknown"
 model_path: str = ""
 wasp_alert: bool = False

 @property
 def counts(self) -> Dict[str, int]:
 out: Dict[str, int] = {}
 for d in self.detections:
 out[d.class_name] = out.get(d.class_name, 0) + 1
 return out


def init_npu(model_path: Optional[str] = None):
 """
 Open a Hailo VDevice when the platform SDK and HEF are present.

 Raises FileNotFoundError / ImportError with clear messages otherwise.
 """
 path = model_path or DEFAULT_HEF_PATH
 if not os.path.exists(path):
 raise FileNotFoundError(
 f"Hailo HEF model missing: {path}. "
 "Set STING_HEF_PATH or use YOLO .pt via StingInferenceEngine."
 )
 try:
 from hailo_platform import VDevice # type: ignore
 except ImportError as e:
 raise ImportError(
 "hailo_platform not installed. Install HailoRT on the edge device "
 "or run with YOLO weights instead."
 ) from e

 target = VDevice()
 logger.info("Hailo NPU channel initialised (hef=%s)", path)
 return target


class StingInferenceEngine:
 """
 Cached edge inference engine.

 Usage:
 engine = StingInferenceEngine() # auto-finds best .pt
 result = engine.predict("path/to/image.jpg")
 """

 def __init__(
 self,
 model_path: Optional[str] = None,
 conf: float = 0.25,
 device: str = "",
 imgsz: int = 640,
 data_yaml: str = "config/data.yaml",
 flywheel_path: str = "flywheel_sting_operation.jsonl",
 prefer_hailo: bool = False,
 ):
 self.conf = conf
 self.device = auto_device(device)
 self.imgsz = imgsz
 self.class_names = load_class_names(data_yaml)
 self.flywheel_path = flywheel_path
 self.prefer_hailo = prefer_hailo or os.getenv("STING_PREFER_HAILO", "").lower() in (
 "1",
 "true",
 "yes",
 )

 self.model_path = model_path or find_best_model()
 self._yolo = None
 self._hailo = None
 self.backend = "uninitialised"

 if self.prefer_hailo:
 try:
 self._hailo = init_npu(os.getenv("STING_HEF_PATH", DEFAULT_HEF_PATH))
 self.backend = "hailo"
 self.model_path = os.getenv("STING_HEF_PATH", DEFAULT_HEF_PATH)
 logger.info("Using Hailo-10H backend")
 return
 except (FileNotFoundError, ImportError) as e:
 logger.warning("Hailo unavailable (%s); falling back to YOLO", e)

 if not self.model_path:
 raise FileNotFoundError(
 "No YOLO weights found. Train a model or set STING_MODEL_PATH."
 )
 self.backend = "yolo"
 logger.info(
 "YOLO backend ready (model=%s device=%s imgsz=%s conf=%s)",
 self.model_path,
 self.device,
 self.imgsz,
 self.conf,
 )

 def _load_yolo(self):
 if self._yolo is None:
 from ultralytics import YOLO

 self._yolo = YOLO(self.model_path)
 logger.info("Loaded YOLO weights: %s", self.model_path)
 return self._yolo

 def predict(
 self,
 source: Union[str, Path],
 conf: Optional[float] = None,
 save: bool = False,
 ) -> InferenceResult:
 """Run inference on an image, directory, or video source."""
 source_str = str(source)
 conf = self.conf if conf is None else conf
 t0 = time.perf_counter()

 if self.backend == "hailo":
 # Hailo full HEF pipeline depends on site-specific HEF IO binding.
 # Surface a clear result rather than crashing the edge loop.
 latency = time.perf_counter() - t0
 logger.warning(
 "Hailo HEF forward path is site-configured; "
 "returning empty detections until HEF graph is bound."
 )
 return InferenceResult(
 source=source_str,
 detections=[],
 latency_seconds=latency,
 backend="hailo",
 model_path=self.model_path or "",
 wasp_alert=False,
 )

 model = self._load_yolo()
 # half precision only helps on CUDA
 use_half = self.device not in ("", "cpu", "mps")
 raw_results = model.predict(
 source=source_str,
 conf=conf,
 save=save,
 device=self.device,
 imgsz=self.imgsz,
 half=use_half,
 verbose=False,
 )
 latency = time.perf_counter() - t0

 detections: List[Detection] = []
 # Ultralytics may return a list (multi-image) - flatten carefully
 results_list = raw_results if isinstance(raw_results, (list, tuple)) else [raw_results]
 for result in results_list:
 names = getattr(result, "names", None) or self.class_names
 boxes = getattr(result, "boxes", None)
 if boxes is None or len(boxes) == 0:
 continue
 for box in boxes:
 cls_id = int(box.cls[0])
 conf_v = float(box.conf[0])
 name = names.get(cls_id, self.class_names.get(cls_id, str(cls_id)))
 xyxy = None
 try:
 xyxy = [float(x) for x in box.xyxy[0].tolist()]
 except Exception:
 xyxy = None
 detections.append(
 Detection(
 class_id=cls_id,
 class_name=str(name),
 confidence=conf_v,
 bbox=xyxy,
 is_wasp=is_wasp_class(str(name)),
 )
 )

 wasp_alert = any(d.is_wasp and d.confidence >= conf for d in detections)
 result = InferenceResult(
 source=source_str,
 detections=detections,
 latency_seconds=round(latency, 4),
 backend=self.backend,
 model_path=self.model_path or "",
 wasp_alert=wasp_alert,
 )
 return result

 def predict_many(
 self,
 sources: Sequence[Union[str, Path]],
 conf: Optional[float] = None,
 save: bool = False,
 ) -> List[InferenceResult]:
 """Predict over multiple sources, reusing the loaded model."""
 return [self.predict(s, conf=conf, save=save) for s in sources]

 def record_flywheel(self, result: InferenceResult, extra: Optional[dict] = None) -> None:
 """Best-effort flywheel write + rotation (never raises)."""
 try:
 from coastal_alpine_core import DataFlywheel, Trajectory
 from datetime import datetime
 import uuid

 flywheel = DataFlywheel(storage_path=self.flywheel_path)
 total = len(result.detections)
 avg_conf = (
 sum(d.confidence for d in result.detections) / total if total else 0.0
 )
 meta = {
 "model_path": result.model_path,
 "backend": result.backend,
 "total_detections": total,
 "avg_confidence": round(avg_conf, 3),
 "counts": result.counts,
 "wasp_alert": result.wasp_alert,
 "source": result.source,
 }
 if extra:
 meta.update(extra)
 traj = Trajectory(
 trajectory_id=str(uuid.uuid4()),
 timestamp=datetime.now().isoformat(),
 action="sting_inference",
 input_summary=f"Source: {result.source}",
 output_summary=(
 f"Detections: {total}, Avg Conf: {avg_conf:.2f}, "
 f"WaspAlert: {result.wasp_alert}"
 ),
 outcome="wasp_alert"
 if result.wasp_alert
 else ("success" if total > 0 else "no_detection"),
 latency_seconds=result.latency_seconds,
 estimated_energy_joules=0.0,
 metadata=meta,
 )
 flywheel.record_trajectory(traj)
 rotate_flywheel_if_needed(self.flywheel_path)
 except Exception as e:
 logger.warning("Flywheel recording failed: %s", e)


# Back-compat for older imports
def create_engine(**kwargs) -> StingInferenceEngine:
 return StingInferenceEngine(**kwargs)
