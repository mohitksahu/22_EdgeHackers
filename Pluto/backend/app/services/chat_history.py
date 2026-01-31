"""
Chat History Manager - Persist conversation history
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.core.logging_config import get_safe_logger

logger = get_safe_logger(__name__)


class ChatHistoryManager:
    """Manage chat history persistence"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatHistoryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.storage_dir = settings.data_dir / "chat_history"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        
        logger.info(f"ChatHistoryManager initialized with storage: {self.storage_dir}")
    
    def _get_session_file(self, session_id: str) -> Path:
        """Get file path for session"""
        safe_id = "".join(c for c in session_id if c.isalnum() or c in '-_')
        return self.storage_dir / f"{safe_id}.json"
    
    def get_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get conversation history for session"""
        file_path = self._get_session_file(session_id)
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                turns = data.get('turns', [])
                return turns[-limit:] if limit else turns
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []
    
    def add_turn(
        self,
        session_id: str,
        query: str,
        response: str,
        sources: List[Dict] = None
    ):
        """Add a conversation turn"""
        file_path = self._get_session_file(session_id)
        
        # Load existing or create new
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {'session_id': session_id, 'turns': [], 'created': datetime.now().isoformat()}
        
        # Add turn
        turn = {
            'turn_number': len(data['turns']) + 1,
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'sources': sources or []
        }
        
        data['turns'].append(turn)
        data['updated'] = datetime.now().isoformat()
        
        # Save
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved turn {turn['turn_number']} for session {session_id}")
    
    def clear_session(self, session_id: str):
        """Clear history for a session"""
        file_path = self._get_session_file(session_id)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleared history for session {session_id}")