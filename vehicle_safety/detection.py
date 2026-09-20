from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import cv2
import numpy as np

from .config import DEFAULT_CONFIG, SafetyConfig

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:
    mp = None
    python = None
    vision = None


@dataclass(frozen=True)
class DrowsinessResult:
    status: str
    score: float
    face_count: int
    eye_count: int
    message: str
    backend: str = "none"
    eye_opening: float = 0.0
    eyes_closed_seconds: float = 0.0
    yawning: bool = False


def _distance(a: object, b: object) -> float:
    return float(np.hypot(a.x - b.x, a.y - b.y))


class DrowsinessAnalyzer:
    """Stateful Face Landmarker analyzer for continuous video frames.

    Eye closure is accumulated by timestamp. A short closure is treated as a
    blink; only closure longer than the configured duration becomes DROWSY.
    """

    def __init__(self, config: SafetyConfig = DEFAULT_CONFIG, model_path: Path | None = None) -> None:
        self.config = config
        self.model_path = model_path or Path(__file__).parents[1] / "models" / "face_landmarker.task"
        self._landmarker = None
        self._closed_since: int | None = None
        self._last_timestamp = -1
        self._lock = Lock()
        self.latest = DrowsinessResult("NO FACE", 0.0, 0, 0, "Start the webcam to monitor the driver.")
        if python is None or vision is None:
            raise RuntimeError("MediaPipe Tasks is not installed.")
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Face Landmarker model not found: {self.model_path}")
        options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(self.model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def close(self) -> None:
        if self._landmarker is not None and hasattr(self._landmarker, "close"):
            self._landmarker.close()

    def process(self, frame: np.ndarray, timestamp_ms: int) -> DrowsinessResult:
        with self._lock:
            if timestamp_ms <= self._last_timestamp:
                timestamp_ms = self._last_timestamp + 1
            self._last_timestamp = timestamp_ms
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
            if not result.face_landmarks:
                self._closed_since = None
                self.latest = DrowsinessResult("NO FACE", 0.0, 0, 0, "No face detected.", "mediapipe")
                return self.latest

            landmarks = result.face_landmarks[0]
            left_open = _distance(landmarks[159], landmarks[145]) / max(_distance(landmarks[33], landmarks[133]), 1e-6)
            right_open = _distance(landmarks[386], landmarks[374]) / max(_distance(landmarks[362], landmarks[263]), 1e-6)
            eye_opening = (left_open + right_open) / 2
            mouth_opening = _distance(landmarks[13], landmarks[14]) / max(_distance(landmarks[61], landmarks[291]), 1e-6)
            now_seconds = timestamp_ms / 1000
            if eye_opening < self.config.eye_closure_ratio:
                self._closed_since = self._closed_since or timestamp_ms
            else:
                self._closed_since = None
            closed_seconds = 0.0 if self._closed_since is None else now_seconds - self._closed_since / 1000
            yawning = mouth_opening > self.config.yawn_ratio
            drowsy = closed_seconds >= self.config.drowsiness_closure_seconds or yawning
            score = min(100.0, (closed_seconds / self.config.drowsiness_closure_seconds) * 100 if self.config.drowsiness_closure_seconds else 0.0)
            if yawning:
                score = max(score, self.config.yawn_score)
            status = "DROWSY" if drowsy else "ALERT"
            message = "Prolonged eye closure or yawning detected." if drowsy else "Eyes open; normal blinking is allowed."
            self.latest = DrowsinessResult(status, score, 1, 2, message, "mediapipe-tasks", eye_opening, closed_seconds, yawning)
            return self.latest


def analyze_frame(frame: np.ndarray) -> DrowsinessResult:
    """Compatibility one-frame entry point used by existing callers/tests."""
    if frame is None or frame.size == 0:
        return DrowsinessResult("NO FACE", 0.0, 0, 0, "No camera frame received.")
    try:
        analyzer = DrowsinessAnalyzer()
        try:
            return analyzer.process(frame, 0)
        finally:
            analyzer.close()
    except (FileNotFoundError, RuntimeError, ValueError, cv2.error):
        return DrowsinessResult("NO FACE", 0.0, 0, 0, "Face Landmarker could not analyze this frame.", "unavailable")
