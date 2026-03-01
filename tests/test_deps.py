"""Tests for Dependency Injection helpers and ConnectionManager."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from skaro_web.api.deps import ConnectionManager


# ═══════════════════════════════════════════════════
# ConnectionManager
# ═══════════════════════════════════════════════════

class TestConnectionManager:

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect(ws)
        ws.accept.assert_awaited_once()
        assert ws in manager._connections

        await manager.disconnect(ws)
        assert ws not in manager._connections

    @pytest.mark.asyncio
    async def test_disconnect_missing_ws_is_safe(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        # Should not raise
        await manager.disconnect(ws)

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self):
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.broadcast({"event": "test"})

        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_awaited_once()
        # Both receive same JSON
        import json
        expected = json.dumps({"event": "test"})
        ws1.send_text.assert_awaited_with(expected)
        ws2.send_text.assert_awaited_with(expected)

    @pytest.mark.asyncio
    async def test_broadcast_removes_stale_connections(self):
        manager = ConnectionManager()
        good_ws = AsyncMock()
        bad_ws = AsyncMock()
        bad_ws.send_text.side_effect = RuntimeError("Connection closed")

        await manager.connect(good_ws)
        await manager.connect(bad_ws)
        assert len(manager._connections) == 2

        await manager.broadcast({"event": "test"})

        # Stale connection removed
        assert len(manager._connections) == 1
        assert good_ws in manager._connections
        assert bad_ws not in manager._connections

    @pytest.mark.asyncio
    async def test_broadcast_empty_connections(self):
        manager = ConnectionManager()
        # Should not raise
        await manager.broadcast({"event": "noop"})

    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect(self):
        """Multiple concurrent connect/disconnect ops should not corrupt state."""
        manager = ConnectionManager()
        sockets = [AsyncMock() for _ in range(20)]

        # Connect all concurrently
        await asyncio.gather(*(manager.connect(ws) for ws in sockets))
        assert len(manager._connections) == 20

        # Disconnect half concurrently
        await asyncio.gather(*(manager.disconnect(ws) for ws in sockets[:10]))
        assert len(manager._connections) == 10
