"""
Optimized MCP session management for high-performance agent node handling.
Provides connection pooling, caching, and async optimization for MCP operations.
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.core.utils.settings import get_settings
# from src.core.redis_cache import redis_graph_cache

logger = logging.getLogger(__name__)

@dataclass
class MCPSession:
    """Represents an MCP session with metadata."""
    client: MultiServerMCPClient
    tools: List[Any]
    created_at: float
    last_used: float
    usage_count: int = 0
    is_active: bool = True

@dataclass 
class MCPClientStats:
    """MCP client performance statistics."""
    total_sessions: int = 0
    active_sessions: int = 0
    tool_cache_hits: int = 0
    tool_cache_misses: int = 0
    avg_tool_load_time: float = 0.0
    total_tool_calls: int = 0

class MCPSessionManager:
    """MCP session manager with connection pooling and caching."""
    
    def __init__(self):
        self.settings = get_settings()
        self._session_pool: Dict[str, MCPSession] = {}
        self._tool_cache: Dict[str, List[Any]] = {}
        self._cache_ttl = 300  # 5 minutes tool cache TTL
        self._max_sessions = 10  # Maximum concurrent MCP sessions
        self._lock = asyncio.Lock()
        self._stats = MCPClientStats()
        
    async def get_mcp_session(self, session_key: Optional[str] = None) -> Tuple[MultiServerMCPClient, List[Any]]:
        """
        Get or create an optimized MCP session with connection pooling.
        
        Args:
            session_key: Optional session identifier for session affinity
            
        Returns:
            Tuple of (MCP client, tools list)
        """
        if not session_key:
            session_key = "default"
            
        async with self._lock:
            # Check for existing active session
            if session_key in self._session_pool:
                session = self._session_pool[session_key]
                if session.is_active and self._is_session_valid(session):
                    session.last_used = time.time()
                    session.usage_count += 1
                    logger.debug(f"Reusing MCP session: {session_key}")
                    return session.client, session.tools
                else:
                    # Remove stale session
                    await self._cleanup_session(session_key)
            
            # Create new session
            return await self._create_new_session(session_key)
    
    async def _create_new_session(self, session_key: str) -> Tuple[MultiServerMCPClient, List[Any]]:
        """Create a new optimized MCP session."""
        try:
            # Check session pool limit
            if len(self._session_pool) >= self._max_sessions:
                await self._cleanup_oldest_session()
            
            logger.info(f"Creating new MCP session: {session_key}")
            start_time = time.time()
            
            # Initialize MCP client with optimized configuration
            client = MultiServerMCPClient(
                {
                    "tutornet_mcp_server": {
                        "url": self.settings.mcp_url,
                        "transport": "streamable_http",
                        "timeout": 10.0,
                        "max_connections": 5,
                        "keepalive": True
                    }
                }
            )
            
            # Load tools with caching
            tools = await self._load_tools_cached(client, session_key)
            
            # Create session object
            session = MCPSession(
                client=client,
                tools=tools,
                created_at=time.time(),
                last_used=time.time()
            )
            
            self._session_pool[session_key] = session
            self._stats.total_sessions += 1
            self._stats.active_sessions += 1
            
            load_time = time.time() - start_time
            logger.info(f"MCP session {session_key} created in {load_time:.2f}s with {len(tools)} tools")
            
            return client, tools
            
        except Exception as e:
            logger.error(f"Failed to create MCP session {session_key}: {e}")
            # Return empty session for graceful degradation
            return None, []
    
    async def _load_tools_cached(self, client: MultiServerMCPClient, session_key: str) -> List[Any]:
        """Load MCP tools directly from the MCP server without caching."""
        start_time = time.time()
        
        try:
            tools = await client.get_tools()
            load_time = time.time() - start_time
            
            logger.debug(f"Loaded {len(tools)} MCP tools for session {session_key} in {load_time:.2f}s (caching bypassed)")
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to load MCP tools for session {session_key}: {e}")
            return []
    
    def _is_session_valid(self, session: MCPSession) -> bool:
        """Check if an MCP session is still valid."""
        max_age = 1800  # 30 minutes
        max_idle = 600   # 10 minutes
        
        current_time = time.time()
        age = current_time - session.created_at
        idle = current_time - session.last_used
        
        return age < max_age and idle < max_idle and session.is_active
    
    async def _cleanup_session(self, session_key: str):
        """Clean up a specific MCP session."""
        if session_key in self._session_pool:
            session = self._session_pool[session_key]
            session.is_active = False
            
            # Attempt graceful client cleanup
            try:
                if hasattr(session.client, 'close'):
                    await session.client.close()
            except Exception as e:
                logger.warning(f"Error closing MCP client: {e}")
            
            del self._session_pool[session_key]
            self._stats.active_sessions -= 1
            logger.debug(f"Cleaned up MCP session: {session_key}")
    
    async def _cleanup_oldest_session(self):
        """Clean up the oldest MCP session when pool is full."""
        if not self._session_pool:
            return
            
        oldest_key = min(
            self._session_pool.keys(),
            key=lambda k: self._session_pool[k].last_used
        )
        await self._cleanup_session(oldest_key)
        logger.info(f"Cleaned up oldest MCP session: {oldest_key}")
    
    # async def invalidate_tool_cache(self, session_key: Optional[str] = None):
    #     """Invalidate MCP tool cache for a specific session or all sessions."""
    #     if session_key:
    #         cache_key = f"mcp_tools:{session_key}"
    #         try:
    #             await redis_graph_cache.invalidate_workflow_cache(cache_key)
    #             logger.info(f"Invalidated MCP tool cache for session: {session_key}")
    #         except Exception as e:
    #             logger.warning(f"Failed to invalidate MCP tool cache: {e}")
    #     else:
    #         # Invalidate all MCP tool caches
    #         pattern = "mcp_tools:*"
    #         # This would require Redis pattern-based deletion
    #         logger.info("Invalidated all MCP tool caches")
    
    async def get_optimized_tools_for_agent(
        self, 
        agent_name: str, 
        tool_configs: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Get optimized MCP tools for a specific agent with session affinity.
        
        Args:
            agent_name: Name of the agent requesting tools
            tool_configs: List of tool configurations from agent
            
        Returns:
            List of optimized MCP tools
        """
        # Use agent name for session affinity
        session_key = f"agent:{agent_name}"
        client, all_tools = await self.get_mcp_session(session_key)
        
        if not all_tools:
            return []
        
        # Filter tools based on agent configuration
        requested_tools = []
        mcp_tool_names = {cfg.get("name") for cfg in tool_configs if cfg.get("type") == "MCP"}
        
        for tool in all_tools:
            if hasattr(tool, 'name') and tool.name in mcp_tool_names:
                requested_tools.append(tool)
        
        self._stats.total_tool_calls += len(requested_tools)
        
        logger.debug(
            f"Agent {agent_name} loaded {len(requested_tools)} MCP tools "
            f"from session {session_key}"
        )
        
        return requested_tools
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get MCP manager performance statistics."""
        async with self._lock:
            active_sessions = sum(1 for s in self._session_pool.values() if s.is_active)
            total_usage = sum(s.usage_count for s in self._session_pool.values())
            
            return {
                "total_sessions_created": self._stats.total_sessions,
                "active_sessions": active_sessions,
                "session_pool_size": len(self._session_pool),
                "tool_cache_hit_rate": (
                    self._stats.tool_cache_hits / 
                    max(self._stats.tool_cache_hits + self._stats.tool_cache_misses, 1)
                ) * 100,
                "avg_tool_load_time": self._stats.avg_tool_load_time,
                "total_tool_calls": self._stats.total_tool_calls,
                "total_session_usage": total_usage
            }
    
    async def cleanup_all_sessions(self):
        """Clean up all MCP sessions during shutdown."""
        async with self._lock:
            for session_key in list(self._session_pool.keys()):
                await self._cleanup_session(session_key)
            
            logger.info("All MCP sessions cleaned up")

# Global MCP session manager instance
mcp_session_manager = MCPSessionManager()
