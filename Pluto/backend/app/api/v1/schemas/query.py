"""
Pydantic schemas for query endpoints
"""
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class QueryType(str, Enum):
    """Types of queries supported"""
    TEXT = "text"
    MULTIMODAL = "multimodal"


class QueryRequest(BaseModel):
    """Request schema for querying the system"""
    query: str = Field(..., description="The query text")
    query_type: QueryType = Field(QueryType.TEXT, description="Type of query")
    modality_filter: Optional[List[str]] = Field(None, description="Filter by modalities")
    max_results: Optional[int] = Field(None, description="Maximum number of results to return")
    include_evidence: bool = Field(True, description="Include evidence in response")
    include_citations: bool = Field(True, description="Include citations in response")


class Evidence(BaseModel):
    """Schema for evidence supporting the answer"""
    document_id: str = Field(..., description="Source document identifier")
    modality: str = Field(..., description="Modality of the evidence")
    content: str = Field(..., description="Evidence content")
    confidence_score: float = Field(..., description="Confidence score (0-1)")
    similarity_score: float = Field(..., description="Similarity score to query")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Assumption(BaseModel):
    """Schema for assumptions made in the response"""
    description: str = Field(..., description="Description of the assumption")
    confidence_score: float = Field(..., description="Confidence score (0-1)")
    reasoning: str = Field(..., description="Reasoning behind the assumption")


class Citation(BaseModel):
    """Schema for citations in the response"""
    evidence_id: str = Field(..., description="Reference to evidence")
    text_span: str = Field(..., description="Specific text span being cited")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    timestamp: Optional[float] = Field(None, description="Timestamp if audio/video")


class QueryResponse(BaseModel):
    """Response schema for query results"""
    query_id: str = Field(..., description="Unique identifier for the query")
    answer: str = Field(..., description="Generated answer")
    confidence_score: float = Field(..., description="Overall confidence score (0-1)")
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence")
    assumptions: List[Assumption] = Field(default_factory=list, description="Assumptions made")
    citations: List[Citation] = Field(default_factory=list, description="Citations in the answer")
    processing_time: float = Field(..., description="Time taken to process query (seconds)")
    status: str = Field("success", description="Query status")

    class Config:
        protected_namespaces = ()


class ConflictInfo(BaseModel):
    """Schema for conflict information"""
    conflict_type: str = Field(..., description="Type of conflict detected")
    description: str = Field(..., description="Description of the conflict")
    conflicting_evidence: List[str] = Field(..., description="IDs of conflicting evidence")
    resolution_suggestion: Optional[str] = Field(None, description="Suggested resolution")


class UncertaintyInfo(BaseModel):
    """Schema for uncertainty information"""
    uncertainty_type: str = Field(..., description="Type of uncertainty")
    description: str = Field(..., description="Description of uncertainty")
    confidence_range: tuple[float, float] = Field(..., description="Confidence range (min, max)")


class RefusalReason(str, Enum):
    """Reasons for refusing to answer"""
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    HIGH_UNCERTAINTY = "high_uncertainty"
    HALLUCINATION_RISK = "hallucination_risk"


class RefusalResponse(BaseModel):
    """Response schema when query is refused"""
    query_id: str = Field(..., description="Unique identifier for the query")
    refusal_reason: RefusalReason = Field(..., description="Reason for refusal")
    explanation: str = Field(..., description="Explanation of why the query was refused")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    conflicts: Optional[List[ConflictInfo]] = Field(None, description="Detected conflicts")
    uncertainties: Optional[List[UncertaintyInfo]] = Field(None, description="Detected uncertainties")
    processing_time: float = Field(..., description="Time taken to process query (seconds)")
    status: str = Field("refused", description="Query status")