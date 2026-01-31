"""
Chat History Manager - Persistent conversation storage per session.

Features:
- JSON-based storage per session ID
- Thread-safe operations
- Automatic cleanup of old conversations
- Support for multi-turn dialogue
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
from threading import Lock

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """Manages conversation history for multi-turn dialogue."""
    
    def __init__(self, storage_dir: str = "F:/Pluto/data/chat_history"):
        """
        Initialize chat history manager.
        
        Args:
            storage_dir: Directory to store chat history JSON files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._locks = {}  # Per-session locks for thread safety
        self._global_lock = Lock()
        
        logger.info(f"ChatHistoryManager initialized with storage: {self.storage_dir}")
    
    def _get_session_lock(self, session_id: str) -> Lock:
        """Get or create a lock for the given session."""
        with self._global_lock:
            if session_id not in self._locks:
                self._locks[session_id] = Lock()
            return self._locks[session_id]
    
    def _get_history_path(self, session_id: str) -> Path:
        """Get the file path for a session's history."""
        return self.storage_dir / f"{session_id}.json"
    
    async def save_turn(
        self,
        session_id: str,
        user_query: str,
        system_response: str,
        cited_sources: Optional[List[str]] = None,
        confidence_score: Optional[float] = None,
        is_conflicting: bool = False,
        conflicts: Optional[List[str]] = None
    ) -> None:
        """
        Save a conversation turn to history.
        
        Args:
            session_id: Session identifier
            user_query: User's question
            system_response: System's answer
            cited_sources: List of source citations
            confidence_score: Confidence score (0-1)
            is_conflicting: Whether conflicting evidence was detected
            conflicts: List of conflict descriptions
        """
        lock = self._get_session_lock(session_id)
        
        # Run file I/O in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._save_turn_sync,
            lock,
            session_id,
            user_query,
            system_response,
            cited_sources,
            confidence_score,
            is_conflicting,
            conflicts
        )
    
    def _save_turn_sync(
        self,
        lock: Lock,
        session_id: str,
        user_query: str,
        system_response: str,
        cited_sources: Optional[List[str]],
        confidence_score: Optional[float],
        is_conflicting: bool,
        conflicts: Optional[List[str]]
    ) -> None:
        """Synchronous implementation of save_turn."""
        with lock:
            history_path = self._get_history_path(session_id)
            
            # Load existing history
            if history_path.exists():
                try:
                    with open(history_path, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted history file for session {session_id}, creating new")
                    history = {"session_id": session_id, "turns": []}
            else:
                history = {"session_id": session_id, "turns": []}
            
            # Create new turn
            turn = {
                "turn_id": len(history["turns"]) + 1,
                "timestamp": datetime.utcnow().isoformat(),
                "user_query": user_query,
                "system_response": system_response,
                "cited_sources": cited_sources or [],
                "confidence_score": confidence_score,
                "is_conflicting": is_conflicting,
                "conflicts": conflicts or []
            }
            
            # Append turn
            history["turns"].append(turn)
            
            # Keep only last 50 turns to avoid unbounded growth
            if len(history["turns"]) > 50:
                history["turns"] = history["turns"][-50:]
                logger.info(f"Trimmed history for session {session_id} to last 50 turns")
            
            # Save to disk
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved turn {turn['turn_id']} for session {session_id}")
    
    async def get_history(
        self,
        session_id: str,
        max_turns: int = 10
    ) -> List[Dict]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            max_turns: Maximum number of recent turns to return
            
        Returns:
            List of conversation turns (most recent last)
        """
        lock = self._get_session_lock(session_id)
        
        # Run file I/O in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_history_sync,
            lock,
            session_id,
            max_turns
        )
    
    def _get_history_sync(
        self,
        lock: Lock,
        session_id: str,
        max_turns: int
    ) -> List[Dict]:
        """Synchronous implementation of get_history."""
        with lock:
            history_path = self._get_history_path(session_id)
            
            if not history_path.exists():
                logger.debug(f"No history found for session {session_id}")
                return []
            
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                turns = history.get("turns", [])
                
                # Return last N turns
                if len(turns) > max_turns:
                    turns = turns[-max_turns:]
                
                logger.info(f"Loaded {len(turns)} turns for session {session_id}")
                return turns
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse history for session {session_id}")
                return []
            except Exception as e:
                logger.error(f"Error loading history for session {session_id}: {e}")
                return []
    
    async def clear_session(self, session_id: str) -> bool:
        """
        Clear all history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleared successfully, False otherwise
        """
        lock = self._get_session_lock(session_id)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._clear_session_sync,
            lock,
            session_id
        )
    
    def _clear_session_sync(self, lock: Lock, session_id: str) -> bool:
        """Synchronous implementation of clear_session."""
        with lock:
            history_path = self._get_history_path(session_id)
            
            if history_path.exists():
                try:
                    history_path.unlink()
                    logger.info(f"Cleared history for session {session_id}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to clear history for session {session_id}: {e}")
                    return False
            else:
                logger.debug(f"No history to clear for session {session_id}")
                return True
    
    async def get_session_info(self, session_id: str) -> Dict:
        """
        Get metadata about a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict with session metadata (turn_count, first_query, last_query, etc.)
        """
        history = await self.get_history(session_id, max_turns=1000)  # Get all
        
        if not history:
            return {
                "session_id": session_id,
                "exists": False,
                "turn_count": 0
            }
        
        return {
            "session_id": session_id,
            "exists": True,
            "turn_count": len(history),
            "first_query": history[0]["user_query"] if history else None,
            "last_query": history[-1]["user_query"] if history else None,
            "last_timestamp": history[-1]["timestamp"] if history else None
        }


# Singleton instance
_history_manager = None

def get_history_manager() -> ChatHistoryManager:
    """Get or create the singleton ChatHistoryManager instance."""
    global _history_manager
    if _history_manager is None:
        _history_manager = ChatHistoryManager()
    return _history_manager
