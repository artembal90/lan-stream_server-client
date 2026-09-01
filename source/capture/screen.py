"""Low-overhead Windows desktop capture using mss."""

from __future__ import annotations

import time
from dataclasses import dataclass

import mss
import numpy as np
from av import VideoFrame


@dataclass(frozen=True)
class CaptureConfig:
    monitor: int = 1
    width: int = 1280
    height: int = 720
    fps: int = 30


class ScreenCapture:
    def __init__(self, config: CaptureConfig) -> None:
        self.config = config
        self._sct = mss.mss()
        monitors = self._sct.monitors
        if config.monitor < 1 or config.monitor >= len(monitors):
            raise ValueError(f"monitor must be between 1 and {len(monitors) - 1}")
        self._monitor = monitors[config.monitor]
        self._next_frame = time.perf_counter()

    def grab(self) -> VideoFrame:
        now = time.perf_counter()
        if now < self._next_frame:
            time.sleep(self._next_frame - now)
        self._next_frame = max(self._next_frame + 1.0 / self.config.fps, time.perf_counter())

        shot = self._sct.grab(self._monitor)
        image = np.asarray(shot, dtype=np.uint8)
        frame = VideoFrame.from_ndarray(image, format="bgra")
        frame.pts = time.monotonic_ns() // 1_000_000
        frame.time_base = __import__("fractions").Fraction(1, 1000)
        if shot.width != self.config.width or shot.height != self.config.height:
            frame = frame.reformat(width=self.config.width, height=self.config.height, format="yuv420p")
        return frame

    def close(self) -> None:
        self._sct.close()
