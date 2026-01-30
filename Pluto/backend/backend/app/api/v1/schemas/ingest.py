"""
Pydantic schemas for ingestion endpoints
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Modality(str, Enum):
    """Supported modalities for ingestion"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"


class IngestRequest(BaseModel):
    """Request schema for document ingestion"""
    modality: Modality = Field(..., description="The modality of the content")
    title: Optional[str] = Field(None, description="Optional title for the document")
    description: Optional[str] = Field(None, description="Optional description")
    tags: Optional[List[str]] = Field(default_factory=list, description="Optional tags")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class IngestResponse(BaseModel):
    """Response schema for successful ingestion"""
    document_id: str = Field(..., description="Unique identifier for the ingested document")
    modality: Modality = Field(..., description="The modality that was processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    embeddings_generated: int = Field(..., description="Number of embeddings generated")
    status: str = Field("success", description="Ingestion status")


class BatchIngestRequest(BaseModel):
    """Request schema for batch ingestion"""
    documents: List[IngestRequest] = Field(..., description="List of documents to ingest")


class BatchIngestResponse(BaseModel):
    """Response schema for batch ingestion"""
    total_documents: int = Field(..., description="Total number of documents processed")
    successful_ingests: int = Field(..., description="Number of successful ingestions")
    failed_ingests: int = Field(..., description="Number of failed ingestions")
    results: List[IngestResponse] = Field(..., description="Detailed results for each document")


class IngestStatus(str, Enum):
    """Status of ingestion process"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestStatusResponse(BaseModel):
    """Response schema for ingestion status"""
    document_id: str = Field(..., description="Document identifier")
    status: IngestStatus = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")