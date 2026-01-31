"""
Query API Endpoint - Handle user queries with retrieval and synthesis
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging_config import get_safe_logger
from app.graph.agents.synthesis_agent import SynthesisAgent
from app.services.chat_history import ChatHistoryManager

logger = get_safe_logger(__name__)
router = APIRouter()

# Initialize components
synthesis_agent = SynthesisAgent()
chat_history = ChatHistoryManager()


class QueryRequest(BaseModel):
    query: str
    session_id: str
    include_sources: bool = True
    max_results: int = 10


class Source(BaseModel):
    file: str
    page: Optional[int] = None
    modality: str
    score: float


class QueryResponse(BaseModel):
    response: str
    sources: List[Source]
    confidence: float
    has_context: bool
    has_conflicts: bool = False
    session_id: str


@router.post("/", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a query against the knowledge base
    
    Returns a grounded response with source citations
    """
    logger.info(f"Query received: {request.query[:50]}... (session: {request.session_id})")
    
    try:
        # Get chat history for context
        history = chat_history.get_history(request.session_id, limit=5)
        
        # Generate response
        result = synthesis_agent.synthesize(
            query=request.query,
            session_id=request.session_id,
            chat_history=history,
            include_sources=request.include_sources
        )
        
        # Format sources
        sources = [
            Source(
                file=s.get('file', 'Unknown'),
                page=s.get('page'),
                modality=s.get('modality', 'text'),
                score=s.get('score', 0.0)
            )
            for s in result.get('sources', [])
        ]
        
        # Save to history
        chat_history.add_turn(
            session_id=request.session_id,
            query=request.query,
            response=result.get('response', ''),
            sources=[s.dict() for s in sources]
        )
        
        return QueryResponse(
            response=result.get('response', ''),
            sources=sources,
            confidence=result.get('confidence', 0.0),
            has_context=result.get('has_context', False),
            has_conflicts=result.get('has_conflicts', False),
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}