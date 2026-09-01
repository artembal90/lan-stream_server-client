"""HTTP API for discovering registered stream sources."""

from __future__ import annotations

from aiohttp import web

from server.signaling.registry import StreamRegistry


registry = StreamRegistry()


async def sources(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "sources": [
                {
                    "source_id": source.source_id,
                    "name": source.name,
                    "connected_at": source.connected_at.isoformat(),
                }
                for source in registry.list_sources()
            ]
        }
    )
