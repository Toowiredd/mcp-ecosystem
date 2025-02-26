from typing import Dict, List, Optional
import time
import json
import asyncio
from neo4j_manager import Neo4jManager
import logging

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        self.neo4j = Neo4jManager()
        self.subscribers = []
        self._context_cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def update_context(self, session_id: str, context_type: str, content: Dict):
        """Update context and notify subscribers"""
        timestamp = time.time() * 1000  # milliseconds
        
        # Save to Neo4j
        try:
            self.neo4j.save_context(session_id, context_type, content, timestamp)
            
            # Update cache
            cache_key = f"{session_id}:{context_type}"
            self._context_cache[cache_key] = {
                "content": content,
                "timestamp": timestamp,
                "expires": timestamp + (self._cache_ttl * 1000)
            }
            
            # Notify subscribers
            update_message = {
                "type": "context_update",
                "session_id": session_id,
                "context_type": context_type,
                "content": content,
                "timestamp": timestamp
            }
            await self._notify_subscribers(update_message)
            
            return True
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
            return False

    async def get_context(self, session_id: str, context_type: Optional[str] = None) -> List[Dict]:
        """Get context from cache or Neo4j"""
        try:
            if context_type:
                cache_key = f"{session_id}:{context_type}"
                cached = self._context_cache.get(cache_key)
                
                if cached and cached["expires"] > (time.time() * 1000):
                    return [{
                        "type": context_type,
                        "content": cached["content"],
                        "timestamp": cached["timestamp"]
                    }]

            # Get from Neo4j if not in cache or if requesting all types
            contexts = self.neo4j.get_context(session_id, context_type)
            
            # Update cache for specific context type
            if context_type and contexts:
                cache_key = f"{session_id}:{context_type}"
                self._context_cache[cache_key] = {
                    "content": contexts[0]["content"],
                    "timestamp": contexts[0]["timestamp"],
                    "expires": time.time() * 1000 + (self._cache_ttl * 1000)
                }
            
            return contexts
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            return []

    async def get_related_contexts(self, session_id: str, context_type: str, max_depth: int = 2) -> List[Dict]:
        """Get related contexts with specified depth"""
        try:
            return self.neo4j.get_related_contexts(session_id, context_type, max_depth)
        except Exception as e:
            logger.error(f"Error getting related contexts: {str(e)}")
            return []

    def subscribe(self, callback):
        """Add subscriber for context updates"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def unsubscribe(self, callback):
        """Remove subscriber"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def _notify_subscribers(self, message: Dict):
        """Notify all subscribers of context updates"""
        for callback in self.subscribers:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {str(e)}")
                # Consider removing failed subscribers
                self.unsubscribe(callback)

    def cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time() * 1000
        expired_keys = [
            key for key, value in self._context_cache.items()
            if value["expires"] < current_time
        ]
        for key in expired_keys:
            del self._context_cache[key]

    async def start_cache_cleanup(self, interval: int = 60):
        """Start periodic cache cleanup"""
        while True:
            self.cleanup_cache()
            await asyncio.sleep(interval)

    def close(self):
        """Close Neo4j connection"""
        self.neo4j.close()
