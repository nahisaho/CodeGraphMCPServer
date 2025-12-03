"""
Engine Manager Unit Tests
=========================

EngineManagerのシングルトン管理とキャッシュのテスト。
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temporary repository with index."""
    codegraph_dir = tmp_path / ".codegraph"
    codegraph_dir.mkdir()
    return tmp_path


class TestEngineManagerSingleton:
    """EngineManagerシングルトンのテスト"""

    @pytest.mark.asyncio
    async def test_get_instance_returns_same_instance(self, temp_repo: Path):
        """Same repo path returns same manager instance."""
        from codegraph_mcp.core.engine_manager import EngineManager

        # Clear any existing instances
        EngineManager._instances.clear()

        manager1 = await EngineManager.get_instance(temp_repo)
        manager2 = await EngineManager.get_instance(temp_repo)

        assert manager1 is manager2

        # Cleanup
        await EngineManager.close_all()

    @pytest.mark.asyncio
    async def test_different_paths_return_different_instances(self, tmp_path: Path):
        """Different repo paths return different manager instances."""
        from codegraph_mcp.core.engine_manager import EngineManager

        # Clear any existing instances
        EngineManager._instances.clear()

        repo1 = tmp_path / "repo1"
        repo2 = tmp_path / "repo2"
        repo1.mkdir()
        repo2.mkdir()

        manager1 = await EngineManager.get_instance(repo1)
        manager2 = await EngineManager.get_instance(repo2)

        assert manager1 is not manager2

        # Cleanup
        await EngineManager.close_all()

    @pytest.mark.asyncio
    async def test_close_all_clears_instances(self, temp_repo: Path):
        """close_all clears all manager instances."""
        from codegraph_mcp.core.engine_manager import EngineManager

        EngineManager._instances.clear()

        await EngineManager.get_instance(temp_repo)
        assert len(EngineManager._instances) == 1

        await EngineManager.close_all()
        assert len(EngineManager._instances) == 0


class TestEngineManagerCache:
    """EngineManagerキャッシュのテスト"""

    @pytest.mark.asyncio
    async def test_statistics_cache(self, temp_repo: Path):
        """Statistics are cached for TTL period."""
        from codegraph_mcp.core.engine_manager import EngineManager

        EngineManager._instances.clear()

        manager = await EngineManager.get_instance(temp_repo)

        # Mock the engine
        mock_engine = AsyncMock()
        mock_stats = MagicMock()
        mock_stats.entity_count = 100
        mock_engine.get_statistics.return_value = mock_stats
        mock_engine.initialize = AsyncMock()

        manager._engine = mock_engine
        manager._initialized = True

        # First call should hit the database
        stats1 = await manager.get_statistics_cached()
        assert mock_engine.get_statistics.call_count == 1

        # Second call should use cache
        stats2 = await manager.get_statistics_cached()
        assert mock_engine.get_statistics.call_count == 1  # Still 1
        assert stats1 is stats2

        await EngineManager.close_all()

    @pytest.mark.asyncio
    async def test_entity_cache(self, temp_repo: Path):
        """Entities are cached after first fetch."""
        from codegraph_mcp.core.engine_manager import EngineManager

        EngineManager._instances.clear()

        manager = await EngineManager.get_instance(temp_repo)

        # Mock the engine
        mock_engine = AsyncMock()
        mock_entity = MagicMock()
        mock_entity.id = "test_entity"
        mock_engine.get_entity.return_value = mock_entity
        mock_engine.initialize = AsyncMock()

        manager._engine = mock_engine
        manager._initialized = True

        # First call should hit the database
        entity1 = await manager.get_entity_cached("test_entity")
        assert mock_engine.get_entity.call_count == 1

        # Second call should use cache
        entity2 = await manager.get_entity_cached("test_entity")
        assert mock_engine.get_entity.call_count == 1  # Still 1
        assert entity1 is entity2

        await EngineManager.close_all()

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, temp_repo: Path):
        """invalidate_cache clears all caches."""
        from codegraph_mcp.core.engine_manager import EngineManager

        EngineManager._instances.clear()

        manager = await EngineManager.get_instance(temp_repo)

        # Add some cached data
        manager._entity_cache["test"] = MagicMock()
        manager._stats_cache = MagicMock()
        manager._stats_cache_time = 100

        # Invalidate
        manager.invalidate_cache()

        assert len(manager._entity_cache) == 0
        assert manager._stats_cache is None
        assert manager._stats_cache_time == 0

        await EngineManager.close_all()

    @pytest.mark.asyncio
    async def test_entity_cache_size_limit(self, temp_repo: Path):
        """Entity cache is limited to 1000 entries."""
        from codegraph_mcp.core.engine_manager import EngineManager

        EngineManager._instances.clear()

        manager = await EngineManager.get_instance(temp_repo)

        # Mock the engine
        mock_engine = AsyncMock()
        mock_engine.get_entity.return_value = None
        mock_engine.initialize = AsyncMock()

        manager._engine = mock_engine
        manager._initialized = True

        # Fill cache beyond limit
        for i in range(1100):
            manager._entity_cache[f"entity_{i}"] = MagicMock()

        # Trigger cache cleanup by fetching a new entity
        await manager.get_entity_cached("new_entity")

        # Cache should be pruned
        assert len(manager._entity_cache) < 1100

        await EngineManager.close_all()


class TestEngineManagerHealthcheck:
    """EngineManagerヘルスチェックのテスト"""

    @pytest.mark.asyncio
    async def test_healthcheck_healthy(self, temp_repo: Path):
        """Healthcheck returns healthy status when connected."""
        from codegraph_mcp.core.engine_manager import EngineManager

        EngineManager._instances.clear()

        manager = await EngineManager.get_instance(temp_repo)

        # Mock the engine
        mock_engine = AsyncMock()
        mock_stats = MagicMock()
        mock_stats.entity_count = 50
        mock_engine.get_statistics.return_value = mock_stats
        mock_engine.initialize = AsyncMock()

        manager._engine = mock_engine
        manager._initialized = True

        health = await manager.healthcheck()

        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert health["entity_count"] == 50

        await EngineManager.close_all()

    @pytest.mark.asyncio
    async def test_healthcheck_unhealthy(self, temp_repo: Path):
        """Healthcheck returns unhealthy status on error."""
        from codegraph_mcp.core.engine_manager import EngineManager

        EngineManager._instances.clear()

        manager = await EngineManager.get_instance(temp_repo)

        # Mock engine that raises an error
        mock_engine = AsyncMock()
        mock_engine.get_statistics.side_effect = Exception("Connection failed")
        mock_engine.initialize = AsyncMock()

        manager._engine = mock_engine
        manager._initialized = True

        health = await manager.healthcheck()

        assert health["status"] == "unhealthy"
        assert health["connected"] is False
        assert "error" in health

        await EngineManager.close_all()


class TestModuleFunctions:
    """モジュールレベル関数のテスト"""

    @pytest.mark.asyncio
    async def test_get_engine_convenience(self, temp_repo: Path):
        """get_engine returns engine instance."""
        from codegraph_mcp.core.engine_manager import EngineManager, get_engine

        EngineManager._instances.clear()

        with patch.object(EngineManager, 'get_instance') as mock_get:
            mock_manager = AsyncMock()
            mock_engine = MagicMock()
            mock_manager.get_engine.return_value = mock_engine
            mock_get.return_value = mock_manager

            engine = await get_engine(temp_repo)

            mock_get.assert_called_once_with(temp_repo)
            mock_manager.get_engine.assert_called_once()
            assert engine is mock_engine

    @pytest.mark.asyncio
    async def test_shutdown_all_calls_close_all(self):
        """shutdown_all delegates to EngineManager.close_all."""
        from codegraph_mcp.core.engine_manager import EngineManager, shutdown_all

        with patch.object(EngineManager, 'close_all', new_callable=AsyncMock) as mock_close:
            await shutdown_all()
            mock_close.assert_called_once()
