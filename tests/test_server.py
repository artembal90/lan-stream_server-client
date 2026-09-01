import pytest
from aiohttp import WSMsgType
from aiohttp.test_utils import TestClient, TestServer

from server.app.main import create_app


@pytest.mark.asyncio
async def test_health_and_sources() -> None:
    app = create_app()
    async with TestServer(app) as server:
        client = TestClient(server)
        await client.start_server()
        health = await client.get("/health")
        assert health.status == 200
        assert (await health.json())["status"] == "ok"

        sources = await client.get("/api/sources")
        assert sources.status == 200
        assert (await sources.json()) == {"sources": []}
        await client.close()


@pytest.mark.asyncio
async def test_websocket_requires_peer_id() -> None:
    app = create_app()
    async with TestServer(app) as server:
        client = TestClient(server)
        await client.start_server()
        ws = await client.ws_connect("/ws")
        message = await ws.receive()
        assert message.type == WSMsgType.CLOSED
        assert ws.close_code == 4001
        await client.close()
