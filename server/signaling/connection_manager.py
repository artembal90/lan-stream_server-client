"""WebSocket connection and signaling message routing."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from aiohttp import WSMsgType, web

from .registry import StreamSource, StreamRegistry


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, web.WebSocketResponse] = {}
        self._sessions: defaultdict[str, set[str]] = defaultdict(set)

    async def connect(self, peer_id: str, ws: web.WebSocketResponse) -> None:
        old = self._connections.get(peer_id)
        if old is not None and not old.closed:
            await old.close(code=4000, message=b"replaced by new connection")
        self._connections[peer_id] = ws

    async def disconnect(self, peer_id: str) -> None:
        self._connections.pop(peer_id, None)
        for peers in self._sessions.values():
            peers.discard(peer_id)

    async def send_to(self, peer_id: str, message: dict[str, Any]) -> bool:
        ws = self._connections.get(peer_id)
        if ws is None or ws.closed:
            return False
        await ws.send_json(message)
        return True

    async def broadcast_session(self, session_id: str, sender_id: str, message: dict[str, Any]) -> None:
        for peer_id in tuple(self._sessions.get(session_id, ())):
            if peer_id != sender_id:
                await self.send_to(peer_id, message)

    def join_session(self, session_id: str, peer_id: str) -> None:
        self._sessions[session_id].add(peer_id)

    def leave_session(self, session_id: str, peer_id: str) -> None:
        peers = self._sessions.get(session_id)
        if peers is None:
            return
        peers.discard(peer_id)
        if not peers:
            self._sessions.pop(session_id, None)

    def get_peer_ids(self) -> list[str]:
        return list(self._connections)


manager = ConnectionManager()


async def signaling(request: web.Request) -> web.WebSocketResponse:
    """Accept registration and route SDP/ICE signaling messages."""
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    peer_id = request.query.get("peer_id")
    if not peer_id:
        await ws.close(code=4001, message=b"peer_id is required")
        return ws

    registry: StreamRegistry = request.app["registry"]
    await manager.connect(peer_id, ws)

    try:
        async for message in ws:
            if message.type != WSMsgType.TEXT:
                if message.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                    break
                continue
            try:
                payload = message.json()
            except ValueError:
                await ws.send_json({"type": "error", "error": "invalid_json"})
                continue
            if not isinstance(payload, dict):
                await ws.send_json({"type": "error", "error": "message_must_be_object"})
                continue

            message_type = payload.get("type")
            target_id = payload.get("target")
            session_id = payload.get("session_id")

            if message_type == "register":
                source_id = str(payload.get("source_id", peer_id))
                registry.register(StreamSource(
                    source_id=source_id,
                    name=str(payload.get("name", source_id)),
                    width=int(payload.get("width", 0)),
                    height=int(payload.get("height", 0)),
                    fps=int(payload.get("fps", 0)),
                    bitrate=int(payload.get("bitrate", 0)),
                ))
                await ws.send_json({"type": "registered", "source_id": source_id})
                continue

            if message_type == "join" and isinstance(session_id, str):
                manager.join_session(session_id, peer_id)
                await ws.send_json({"type": "joined", "session_id": session_id, "peer_id": peer_id})
                continue

            if message_type == "leave" and isinstance(session_id, str):
                manager.leave_session(session_id, peer_id)
                await ws.send_json({"type": "left", "session_id": session_id})
                continue

            if target_id is not None:
                if not isinstance(target_id, str):
                    await ws.send_json({"type": "error", "error": "target_must_be_string"})
                    continue
                forwarded = dict(payload)
                forwarded["sender"] = peer_id
                if not await manager.send_to(target_id, forwarded):
                    await ws.send_json({"type": "error", "error": "target_not_connected", "target": target_id})
                continue

            if isinstance(session_id, str):
                forwarded = dict(payload)
                forwarded["sender"] = peer_id
                await manager.broadcast_session(session_id, peer_id, forwarded)
                continue

            await ws.send_json({"type": "error", "error": "target_or_session_required"})
    finally:
        registry.unregister(peer_id)
        await manager.disconnect(peer_id)

    return ws
