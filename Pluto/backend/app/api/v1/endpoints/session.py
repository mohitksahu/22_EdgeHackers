"""
Session management endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from app.storage.vector_store import VectorStore
from app.storage.chat_store import ChatHistoryManager

logger = logging.getLogger(__name__)

router = APIRouter()
vector_store = VectorStore()
chat_history = ChatHistoryManager()


class SessionClearResponse(BaseModel):
    """Response for session clear operation"""
    status: str
    session_id: str
    message: str


@router.delete("/clear", response_model=SessionClearResponse)
async def clear_session(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Clear all documents and chat history for the current session
    
    - **session_id**: Session to clear (from header)
    """
    try:
        logger.info(f"Clearing session: {session_id}")
        
        # Clear documents from vector store
        deleted_count = vector_store.delete_by_session(session_id)
        
        # Clear chat history
        history_cleared = await chat_history.clear_session(session_id)
        
        return SessionClearResponse(
            status="success",
            session_id=session_id,
            message=f"Session cleared: {deleted_count} documents deleted, chat history cleared"
        )
        
    except Exception as e:
        logger.error(f"Failed to clear session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear session: {str(e)}"
        )


@router.get("/info")
async def get_session_info(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Get information about the current session including chat history
    
    - **session_id**: Session to query (from header)
    """
    try:
        # Get knowledge catalog to count documents
        catalog = vector_store.get_knowledge_catalog()
        
        # Get chat history info
        history_info = await chat_history.get_session_info(session_id)
        
        return {
            "session_id": session_id,
            "document_count": len(catalog.get("topics", [])),
            "topics": catalog.get("topics", []),
            "status": "active",
            "chat_history": {
                "turn_count": history_info.get("turn_count", 0),
                "first_query": history_info.get("first_query"),
                "last_query": history_info.get("last_query"),
                "last_timestamp": history_info.get("last_timestamp")
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get session info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session info: {str(e)}"
        )