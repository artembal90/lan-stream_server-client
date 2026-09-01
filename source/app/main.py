"""LAN Stream desktop source application."""

from __future__ import annotations

import argparse
import asyncio
import logging
import uuid

from aiortc import RTCPeerConnection, RTCRtpSender, RTCSessionDescription

from source.capture.screen import CaptureConfig, ScreenCapture
from source.capture.track import DesktopVideoTrack
from source.webrtc.signaling import SignalingClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lan-stream-source")


async def wait_for_ice(pc: RTCPeerConnection) -> None:
    if pc.iceGatheringState == "complete":
        return
    event = asyncio.Event()

    @pc.on("icegatheringstatechange")
    def on_ice_state_change() -> None:
        if pc.iceGatheringState == "complete":
            event.set()

    await event.wait()


async def run(args: argparse.Namespace) -> None:
    peer_id = args.source_id or f"source-{uuid.uuid4()}"
    signaling = SignalingClient(args.server, peer_id)
    capture = ScreenCapture(CaptureConfig(args.monitor, args.width, args.height, args.fps))
    pcs: set[RTCPeerConnection] = set()

    await signaling.connect()
    await signaling.send({
        "type": "register",
        "source_id": peer_id,
        "name": args.name,
        "width": args.width,
        "height": args.height,
        "fps": args.fps,
        "bitrate": args.bitrate,
    })
    log.info("source %s registered as %s", args.name, peer_id)

    try:
        while True:
            message = await signaling.receive()
            if message is None:
                break
            if message.get("type") != "offer":
                continue

            pc = RTCPeerConnection()
            pcs.add(pc)
            sender = pc.addTrack(DesktopVideoTrack(capture))

            # Prefer H.264 for the first LAN implementation. Hardware encoders
            # are intentionally deferred to the optimization stage.
            h264_codecs = [
                codec for codec in RTCRtpSender.getCapabilities("video").codecs
                if codec.mimeType.lower() == "video/h264"
            ]
            if h264_codecs:
                sender.setCodecPreferences(h264_codecs)

            await pc.setRemoteDescription(
                RTCSessionDescription(
                    sdp=message["sdp"],
                    type=message.get("sdp_type", "offer"),
                )
            )
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await wait_for_ice(pc)

            local = pc.localDescription
            if local is None:
                raise RuntimeError("failed to create local SDP answer")

            await signaling.send({
                "type": "answer",
                "target": message.get("sender"),
                "session_id": message.get("session_id", peer_id),
                "sdp": local.sdp,
                "sdp_type": local.type,
            })
            log.info("answered viewer %s", message.get("sender"))
    finally:
        for pc in pcs:
            await pc.close()
        capture.close()
        await signaling.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAN Stream desktop source")
    parser.add_argument("--server", default="http://127.0.0.1:8080")
    parser.add_argument("--source-id")
    parser.add_argument("--name", default="Desktop")
    parser.add_argument("--monitor", type=int, default=1)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--bitrate", type=int, default=4_000_000)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
