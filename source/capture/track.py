"""aiortc MediaStreamTrack backed by the desktop capture loop."""

from __future__ import annotations

import asyncio

from aiortc import MediaStreamTrack

from .screen import ScreenCapture


class DesktopVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, capture: ScreenCapture) -> None:
        super().__init__()
        self.capture = capture
        self.frames = 0
        self.started = asyncio.get_running_loop().time()

    async def recv(self):
        if self.readyState != "live":
            raise RuntimeError("desktop video track is not live")
        frame = await asyncio.to_thread(self.capture.grab)
        self.frames += 1
        return frame

    def close(self) -> None:
        self.capture.close()
        super().stop()
