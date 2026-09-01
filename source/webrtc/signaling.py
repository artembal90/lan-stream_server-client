"""Small WebSocket signaling client used by the source application."""

from __future__ import annotations

import json
from typing import Any

import aiohttp


class SignalingClient:
    def __init__(self, server_url: str, peer_id: str) -> None:
        self.server_url = server_url.rstrip("/")
        self.peer_id = peer_id
        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None

    async def connect(self) -> None:
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(
            f"{self.server_url}/ws",
            params={"peer_id": self.peer_id},
            heartbeat=30,
        )

    async def send(self, message: dict[str, Any]) -> None:
        if self._ws is None or self._ws.closed:
            raise RuntimeError("signaling client is not connected")
        await self._ws.send_str(json.dumps(message, separators=(",", ":")))

    async def receive(self) -> dict[str, Any] | None:
        if self._ws is None:
            raise RuntimeError("signaling client is not connected")
        message = await self._ws.receive()
        if message.type == aiohttp.WSMsgType.TEXT:
            value = json.loads(message.data)
            if not isinstance(value, dict):
                raise ValueError("signaling message must be an object")
            return value
        return None

    async def close(self) -> None:
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        if self._session is not None:
            await self._session.close()
            self._session = None
            self._ws = None
