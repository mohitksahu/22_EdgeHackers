"""
Query API endpoints
"""
import logging
import uuid
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from app.graph.graph_builder import GraphBuilder
from app.graph.state import GraphState
from app.core.scope_registry import get_last_scope

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize graph
graph_builder = GraphBuilder()
graph = graph_builder.build_graph()


class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    user_id: str = "default_user"


class CitedSource(BaseModel):
    """Individual cited source with multimodal metadata"""
    modality: str = "text"
    content: str = ""
    score: float = 0.0
    filename: str = "Unknown"
    page: Optional[int] = None
    timestamp: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response model - Frontend-compatible structure"""
    query: str
    response: str
    refusal: Optional[str] = None
    confidence_score: float
    cited_sources: List[CitedSource]
    sources: List[str] = []
    conflicts: List[str] = []
    conflicts_detected: bool = False
    processing_time: float = 0.0
    status: str = "success"
    assumptions: List[str] = []
    evidence_grade: float = 0.0
    confidence_per_source: Dict[str, float] = {}


@router.post("/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    x_scope_id: Optional[str] = Header(default=None, alias="X-Scope-Id"),
) -> QueryResponse:
    """
    Query the multimodal RAG system (SCOPE AWARE)
    """

    try:
        # 🔑 SINGLE DOCUMENT MODE: Use the current document scope
        # Since we clear before each upload, there's only one scope
        scope_id = x_scope_id or "single-doc-scope"

        logger.info(
            f"Processing query: '{request.query[:50]}...' | scope_id={scope_id}"
        )

        # Inject scope into graph
        initial_state: GraphState = {
            "query": request.query,
            "scope_id": scope_id,
        }

        # Run graph
        final_state = await graph.ainvoke(initial_state)

        # -----------------------------
        # REFUSAL PATH
        # -----------------------------
        if final_state.get("status") == "refused" or not final_state.get("is_allowed", True):
            refusal_message = final_state.get(
                "final_response", "Unable to answer this query."
            )

            return QueryResponse(
                query=request.query,
                response="",
                refusal=refusal_message,
                confidence_score=0.0,
                cited_sources=[],
                sources=[],
                conflicts=[],
                conflicts_detected=False,
                processing_time=final_state.get("processing_time", 0.0),
                status="refused",
                assumptions=[],
                evidence_grade=0.0,
                confidence_per_source={},
            )

        # -----------------------------
        # SUCCESS PATH
        # -----------------------------
        answer_text = final_state.get("final_response") or (
            "I don't have enough information to answer this question."
        )

        retrieved_docs = final_state.get("retrieved_documents", [])

        cited_sources: List[CitedSource] = []
        source_scores: Dict[str, List[float]] = {}

        for doc in retrieved_docs:
            metadata = doc.get("metadata", {})

            source_file = metadata.get("source_file") or metadata.get("file_name", "Unknown")
            if isinstance(source_file, str):
                source_file = source_file.replace("\\", "/")
                if "/" in source_file:
                    source_file = source_file.split("/")[-1]

            modality = metadata.get("modality", "text")
            score = float(doc.get("score", 0.0))
            score = score if score <= 1.0 else score / 100.0

            source_scores.setdefault(source_file, []).append(score)

            cited_sources.append(
                CitedSource(
                    modality=modality,
                    content=doc.get("content", "")[:500],
                    score=score,
                    filename=source_file,
                    page=metadata.get("page_number"),
                    timestamp=metadata.get("timestamp"),
                )
            )

        confidence_per_source = {
            src: sum(scores) / len(scores)
            for src, scores in source_scores.items()
        }

        evidence_scores = final_state.get("evidence_scores", [])
        global_confidence = (
            sum(evidence_scores) / len(evidence_scores)
            if evidence_scores
            else 0.0
        )

        unique_sources = list(source_scores.keys())

        return QueryResponse(
            query=request.query,
            response=answer_text,
            refusal=None,
            confidence_score=global_confidence,
            cited_sources=cited_sources,
            sources=unique_sources,
            conflicts=final_state.get("conflicts", []),
            conflicts_detected=final_state.get("is_conflicting", False),
            processing_time=final_state.get("processing_time", 0.0),
            status="success",
            assumptions=final_state.get("assumptions", []),
            evidence_grade=global_confidence,
            confidence_per_source=confidence_per_source,
        )

    except Exception as e:
        logger.exception("Query failed")
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}",
        )


@router.get("/health")
async def query_health():
    return {"status": "healthy", "service": "query"}
