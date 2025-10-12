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
# import asyncio
# import time
# import logging
# from typing import Dict, Any, Optional, Tuple
# from dataclasses import dataclass, field
# from sqlalchemy.orm import Session
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
# from langgraph.store.postgres.aio import AsyncPostgresStore

# from src.core.utils.settings import get_settings
# from src.core.redis_cache import redis_graph_cache
# from src.core.config_loader import load_config
# from src.core.utils.exceptions import WorkflowNotFoundError, GraphBuildError
# from src.models.models import WorkflowType

# logger = logging.getLogger(__name__)

# @dataclass
# class CompiledGraphEntry:
#     """Cached compiled graph with metadata."""
#     graph: Any
#     config: Dict[str, Any]
#     created_at: float
#     last_accessed: float
#     access_count: int = 0
#     compilation_time: float = 0

# class GraphCacheManager:
#     """Graph compilation and caching manager with multi-level caching."""
    
#     def __init__(self):
#         self.settings = get_settings()
#         self._compiled_graphs: Dict[str, CompiledGraphEntry] = {}
#         self._checkpointer = None
#         self._store = None
#         self._lock = asyncio.Lock()
#         self._connection_initialized = False
    
#     async def initialize_connections(self):
#         """Initialize persistent PostgreSQL connections."""
#         if not self._connection_initialized:
#             async with self._lock:
#                 if not self._connection_initialized:
#                     try:
#                         # Initialize store and checkpointer with context managers
#                         store_ctx = AsyncPostgresStore.from_conn_string(self.settings.database_url)
#                         checkpointer_ctx = AsyncPostgresSaver.from_conn_string(self.settings.database_url)
                        
#                         self._store = await store_ctx.__aenter__()
#                         self._checkpointer = await checkpointer_ctx.__aenter__()
                        
#                         # Store context managers for cleanup
#                         self._store_ctx = store_ctx
#                         self._checkpointer_ctx = checkpointer_ctx
                        
#                         await self._store.setup()
#                         await self._checkpointer.setup()
                        
#                         self._connection_initialized = True
                        
#                     except Exception as e:
#                         logger.error(f"Failed to initialize PostgreSQL connections: {e}")
#                         raise
    
#     async def close_connections(self):
#         """Close persistent PostgreSQL connections."""
#         if self._connection_initialized:
#             async with self._lock:
#                 if self._connection_initialized:
#                     try:
#                         # Close context managers properly
#                         if hasattr(self, '_store_ctx'):
#                             await self._store_ctx.__aexit__(None, None, None)
#                         if hasattr(self, '_checkpointer_ctx'):
#                             await self._checkpointer_ctx.__aexit__(None, None, None)
                        
#                         self._connection_initialized = False
                        
#                     except Exception as e:
#                         logger.error(f"Error closing PostgreSQL connections: {e}")
    
#     async def get_compiled_graph(self, workflow_id: str, db: Session, is_stream_call: bool = False, x_user_groups: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
#         """Get pre-compiled graph with multi-level caching using Redis for rebuild data."""
#         await self.initialize_connections()
        
#         # Load current config to check for updates
#         current_config = load_config(workflow_id=workflow_id, db=db)
#         if not current_config:
#             logger.warning(f"Workflow {workflow_id} not found during config load.")
#             raise WorkflowNotFoundError(workflow_id)
        
#         updated_at_str = current_config.get("updated_at", "")
#         cache_key = f"{workflow_id}_{updated_at_str}_{'stream' if is_stream_call else 'nonstream'}" # Include stream flag in cache key
#         # Level 1: In-memory cache (fastest)
#         async with self._lock:
#             if cache_key in self._compiled_graphs:
#                 entry = self._compiled_graphs[cache_key]
#                 entry.last_accessed = time.time()
#                 entry.access_count += 1
#                 return entry.graph, entry.config
        
#         # Level 2: Redis cache for build data (fast, shared across pods)
#         # redis_build_data = await redis_graph_cache.get_graph_build_data(workflow_id, updated_at_str)
#         # if redis_build_data:
#         #     # Rebuild graph from cached data
#         #     try:
#         #         start_rebuild = time.perf_counter()
                
#         #         # Extract cached workflow config and build type
#         #         workflow_config = redis_build_data.get("workflow_config")
#         #         build_type = redis_build_data.get("build_type", "langgraph")
                
#         #         if workflow_config:
#         #             # Build graph using cached config
#         #             builder, config = await self._build_graph_from_config(workflow_config, build_type, db, is_stream_call, x_user_groups)
                    
#         #             # Compile with persistent connections
#         #             compiled_graph = builder.compile(
#         #                 checkpointer=self._checkpointer,
#         #                 store=self._store
#         #             )
                    
#         #             rebuild_time = time.perf_counter() - start_rebuild
                    
#         #             # Store in in-memory cache for faster subsequent access
#         #             async with self._lock:
#         #                 self._compiled_graphs[cache_key] = CompiledGraphEntry(
#         #                     graph=compiled_graph,
#         #                     config=config,
#         #                     created_at=time.time(),
#         #                     last_accessed=time.time(),
#         #                     compilation_time=rebuild_time
#         #                 )
                    
#         #             return compiled_graph, config
                    
#         #     except Exception as e:
#         #         logger.warning(f"Failed to rebuild graph from Redis cache: {e}. Falling through to Level 3.")
#         #         # Fall through to Level 3
        
#         # Level 3: Build and compile from scratch (slowest)
#         start_compile = time.perf_counter()
        
#         # Build the graph
#         builder, config = await self._build_graph_internal(workflow_id, db, is_stream_call, x_user_groups)
#         # Compile with persistent connections
#         compiled_graph = builder.compile(
#             checkpointer=self._checkpointer,
#             store=self._store
#         )
        
#         compilation_time = time.perf_counter() - start_compile
        
#         # Cache in memory
#         async with self._lock:
#             self._compiled_graphs[cache_key] = CompiledGraphEntry(
#                 graph=compiled_graph,
#                 config=config,
#                 created_at=time.time(),
#                 last_accessed=time.time(),
#                 compilation_time=compilation_time
#             )
            
#             # Clean old in-memory entries
#             await self._cleanup_old_entries()
        
#         # Cache build data in Redis for other pods (not the compiled object)
#         build_data = {
#             "workflow_config": current_config,
#             "build_type": current_config.get("type", "langgraph"),
#             "updated_at": updated_at_str
#         }
#         await redis_graph_cache.cache_graph_build_data(workflow_id, updated_at_str, build_data)
        
#         return compiled_graph, config
    
#     async def _build_graph_from_config(self, workflow_config: Dict[str, Any], build_type: str, db: Session, is_stream_call: bool = False, x_user_groups: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
#         """
#         Build graph from cached configuration data.
        
#         Note: This method is limited because it doesn't have access to the database session.
#         For complex builds that require DB access, we fall back to fresh building.
#         """
#         from src.core.builders.langgraph_builder import build_langgraph
#         from src.core.builders.supervisor_builder import build_supervisor
#         from src.core.builders.swarm_builder import create_swarm_builder
        
#         if not workflow_config:
#             raise ValueError("Invalid workflow configuration")
        
#         # Note: Most builders require database session for agent/tool loading
#         # This method is a fallback that works for simple cases
#         # Complex workflows will fall through to Level 3 (fresh build with DB)
        
#         try:
#             if build_type == WorkflowType.LANGGRAPH.value:
#                 # Try building without DB session (limited functionality)
#                 builder = await build_langgraph(workflow_config, db, is_stream_call) # Pass db, is_stream_call
#                 return builder, workflow_config
                
#             elif build_type == WorkflowType.SUPERVISOR.value:
#                 node_configs = workflow_config.get("nodes", [])
#                 start_node_id = workflow_config.get("start_node")
#                 builder = await build_supervisor(workflow_config, node_configs, {}, start_node_id, db, is_stream_call, x_user_groups)
#                 return builder, workflow_config
                
#             elif build_type == WorkflowType.SWARM.value:
#                 # Swarm builder requires DB session - cannot rebuild from cache
#                 builder = await create_swarm_builder(workflow_config.get("nodes", []), workflow_config, db, is_stream_call, x_user_groups)
#                 return builder, workflow_config
                
#             else:
#                 # Default to LangGraph
#                 builder = await build_langgraph(workflow_config, db, is_stream_call) # Pass db, is_stream_call
#                 return builder, workflow_config
                
#         except Exception as e:
#             logger.warning(f"Cannot rebuild from cache (DB session required): {e}")
#             raise ValueError(f"Rebuild from cache failed: {e}")

#     async def _build_graph_internal(self, workflow_id: str, db: Session, is_stream_call: bool = False, x_user_groups: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
#         """Internal graph building logic with optimizations."""
#         from src.core.builders.langgraph_builder import build_langgraph
#         from src.core.builders.supervisor_builder import build_supervisor
#         from src.core.builders.swarm_builder import create_swarm_builder
        
#         # Check Redis cache for config first
#         cached_config = await redis_graph_cache.get_workflow_config(workflow_id)
#         print(f"Corssing here")
#         if cached_config:
#             current_config = cached_config
#         else:
#             current_config = load_config(workflow_id=workflow_id, db=db)
#             if current_config:
#                 # Cache config for other requests
#                 await redis_graph_cache.cache_workflow_config(workflow_id, current_config)
        
#         if not current_config:
#             raise WorkflowNotFoundError(workflow_id)
        
#         node_configs = current_config.get("nodes", [])
#         start_node_id = current_config.get("start_node")
#         workflow_type = current_config.get("type")
        
#         try:
#             if workflow_type == WorkflowType.SWARM.value:
#                 builder = await create_swarm_builder(node_configs, current_config, db, is_stream_call, x_user_groups=x_user_groups)
#             elif workflow_type == WorkflowType.SUPERVISOR.value:
#                 builder = await build_supervisor(current_config, node_configs, {}, start_node_id, db, is_stream_call, x_user_groups=x_user_groups)
#             else:
#                 builder = await build_langgraph(current_config, db, is_stream_call, x_user_groups=x_user_groups)
#             if builder is None:
#                 raise GraphBuildError(workflow_id, "Builder returned None")
            
#             return builder, current_config
            
#         except Exception as e:
#             logger.exception(f"Failed to build graph for workflow ID: {workflow_id}")
#             raise GraphBuildError(workflow_id, str(e))
    
#     async def _cleanup_old_entries(self):
#         """Remove old unused entries from in-memory cache."""
#         if len(self._compiled_graphs) <= 20:  # Keep reasonable cache size
#             return
        
#         # Sort by last accessed time and remove oldest
#         sorted_entries = sorted(
#             self._compiled_graphs.items(),
#             key=lambda x: x[1].last_accessed
#         )
        
#         # Remove oldest 30% of entries
#         to_remove = len(sorted_entries) // 3
#         for key, _ in sorted_entries[:to_remove]:
#             del self._compiled_graphs[key]
    
#     # async def invalidate_workflow_cache(self, workflow_id: str):
#     #     """Invalidate all cache levels for a workflow."""
#     #     # Clear in-memory cache
#     #     async with self._lock:
#     #         if workflow_id == "*":
#     #             # Wildcard - clear all in-memory cache entries
#     #             self._compiled_graphs.clear()
#     #         else:
#     #             # Specific workflow - clear entries that match
#     #             keys_to_remove = [key for key in self._compiled_graphs.keys() if key.startswith(workflow_id)]
#     #             for key in keys_to_remove:
#     #                 del self._compiled_graphs[key]
        
#     #     # Clear Redis cache
#     #     await redis_graph_cache.invalidate_workflow_cache(workflow_id)
        
    
#     # async def get_cache_stats(self) -> Dict[str, Any]:
#     #     """Get cache performance statistics."""
#     #     async with self._lock:
#     #         total_entries = len(self._compiled_graphs)
#     #         total_accesses = sum(entry.access_count for entry in self._compiled_graphs.values())
#     #         avg_compilation_time = sum(entry.compilation_time for entry in self._compiled_graphs.values()) / max(total_entries, 1)
            
#     #         return {
#     #             "in_memory_entries": total_entries,
#     #             "total_accesses": total_accesses,
#     #             "avg_compilation_time": avg_compilation_time,
#     #             "connection_initialized": self._connection_initialized
#     #         }

# # Global graph cache manager instance
# graph_manager = GraphCacheManager()
