"""
Simplified graph manager without PostgreSQL dependencies.
Handles basic graph caching for development.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimpleGraphEntry:
    """Simple cached graph entry."""
    graph: Any
    config: Dict[str, Any]
    created_at: float
    last_accessed: float


class SimpleGraphCacheManager:
    """Simple graph cache manager without PostgreSQL dependencies."""
    
    def __init__(self):
        self._compiled_graphs: Dict[str, SimpleGraphEntry] = {}
        self._lock = asyncio.Lock()
        self._connection_initialized = False
    
    async def initialize_connections(self):
        """Initialize connections (no-op for simple implementation)."""
        if not self._connection_initialized:
            async with self._lock:
                self._connection_initialized = True
                logger.info("Simple graph cache manager initialized (no database)")
    
    async def close_connections(self):
        """Close connections (no-op for simple implementation)."""
        async with self._lock:
            self._connection_initialized = False
            logger.info("Simple graph cache manager connections closed")
    
    async def get_compiled_graph(self, workflow_type: str, config: Dict[str, Any]) -> Optional[Any]:
        """Get a compiled graph from cache."""
        cache_key = f"{workflow_type}_{hash(str(sorted(config.items())))}"
        async with self._lock:
            if cache_key in self._compiled_graphs:
                entry = self._compiled_graphs[cache_key]
                entry.last_accessed = asyncio.get_event_loop().time()
                logger.debug(f"Retrieved compiled graph from cache: {workflow_type}")
                return entry.graph
        return None
    
    async def cache_compiled_graph(self, workflow_type: str, config: Dict[str, Any], graph: Any):
        """Cache a compiled graph."""
        cache_key = f"{workflow_type}_{hash(str(sorted(config.items())))}"
        current_time = asyncio.get_event_loop().time()
        
        async with self._lock:
            self._compiled_graphs[cache_key] = SimpleGraphEntry(
                graph=graph,
                config=config,
                created_at=current_time,
                last_accessed=current_time
            )
            logger.debug(f"Cached compiled graph: {workflow_type}")
    
    async def clear_cache(self):
        """Clear all cached graphs."""
        async with self._lock:
            self._compiled_graphs.clear()
            logger.info("Graph cache cleared")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            return {
                "in_memory_entries": len(self._compiled_graphs),
                "connection_initialized": self._connection_initialized
            }


# Global graph cache manager instance
graph_manager = SimpleGraphCacheManager()