import time

import av
import cv2
from streamlit_webrtc import VideoProcessorBase

from .config import DEFAULT_CONFIG
from .detection import DrowsinessAnalyzer, DrowsinessResult


class DriverVideoProcessor(VideoProcessorBase):
    """WebRTC frame processor; no Streamlit calls are made on the worker thread."""

    def __init__(self) -> None:
        self.analyzer = DrowsinessAnalyzer(DEFAULT_CONFIG)
        self.latest = self.analyzer.latest

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image = frame.to_ndarray(format="bgr24")
        timestamp_ms = int(time.monotonic() * 1000)
        self.latest = self.analyzer.process(image, timestamp_ms)
        color = (0, 0, 255) if self.latest.status == "DROWSY" else (0, 180, 0)
        cv2.putText(image, f"{self.latest.status}  {self.latest.score:.0f}/100", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
        return av.VideoFrame.from_ndarray(image, format="bgr24")

    def __del__(self) -> None:
        try:
            self.analyzer.close()
        except (AttributeError, RuntimeError):
            pass
