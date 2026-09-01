"""WebRTC peer foundation for a source publisher."""

from __future__ import annotations

from aiortc import RTCPeerConnection, RTCSessionDescription


class SourcePeer:
    def __init__(self) -> None:
        self.connection = RTCPeerConnection()

    async def create_offer(self) -> RTCSessionDescription:
        offer = await self.connection.createOffer()
        await self.connection.setLocalDescription(offer)
        if self.connection.localDescription is None:
            raise RuntimeError("failed to create local SDP description")
        return self.connection.localDescription

    async def accept_answer(self, sdp: str, sdp_type: str = "answer") -> None:
        await self.connection.setRemoteDescription(
            RTCSessionDescription(sdp=sdp, type=sdp_type)
        )

    async def add_ice_candidate(self, candidate) -> None:
        """ICE candidate handling will be wired to aiortc candidate objects."""
        await self.connection.addIceCandidate(candidate)

    async def close(self) -> None:
        await self.connection.close()
