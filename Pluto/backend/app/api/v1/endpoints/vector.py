"""
Vector management endpoints
"""
import logging
from typing import Dict, Any, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.storage.vector_store import VectorStore
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.delete("/reset")
async def reset_vector_store() -> Dict[str, Any]:
    """
    Reset the vector store by deleting all embeddings and data.

    This is a destructive operation that cannot be undone.
    Use with caution in development/testing environments.
    """
    try:
        vector_store = VectorStore()
        vector_store.reset()

        logger.info("Vector store reset completed successfully")
        return {
            "status": "success",
            "message": "Vector store has been reset. All embeddings and data have been deleted."
        }

    except Exception as e:
        logger.error(f"Failed to reset vector store: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset vector store: {str(e)}"
        )


@router.get("/stats")
async def get_vector_store_stats() -> Dict[str, Any]:
    """
    Get statistics about the vector store including counts by modality.
    
    Returns:
        Statistics showing total documents and breakdown by modality (text, image, audio)
    """
    try:
        vector_store = VectorStore()
        
        # Get basic stats (total count, collection name, embedding dimension)
        basic_stats = vector_store.get_stats()

        # For Qdrant, we can't easily get all documents with metadata like ChromaDB
        # So we'll use the basic stats for now
        modality_counts = {
            "text": 0,  # TODO: Implement modality counting for Qdrant
            "image": 0,
            "audio": 0
        }
        
        stats = {
            "total_documents": basic_stats.get('total_documents', 0),
            "modalities": modality_counts,
            "collection": basic_stats.get('collection_name', 'unknown')
        }
        
        logger.info(f"Vector store stats: {stats['total_documents']} total docs, {modality_counts}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get vector store stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get vector store stats: {str(e)}"
        )


@router.post("/cleanup-orphans")
async def cleanup_orphaned_documents() -> Dict[str, Any]:
    """
    Clean up orphaned documents whose source files no longer exist on disk.

    This is useful when files were manually deleted but their vectors remain in the vector store.

    Returns:
        Number of orphaned documents deleted and list of cleaned files
    """
    try:
        vector_store = VectorStore()

        # For Qdrant, we need to implement this differently
        # TODO: Implement orphaned document cleanup for Qdrant
        logger.warning("Orphaned document cleanup not yet implemented for Qdrant")

        return {
            "status": "not_implemented",
            "message": "Orphaned document cleanup is not yet implemented for Qdrant",
            "deleted_count": 0,
            "deleted_sources": []
        }
    
    except Exception as e:
        logger.error(f"Failed to cleanup orphaned documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup orphaned documents: {str(e)}"
        )


@router.delete("/source/{source_file:path}")
async def delete_documents_by_source(source_file: str) -> Dict[str, Any]:
    """
    Delete all documents from a specific source file.
    
    Args:
        source_file: Path to the source file (can be relative or absolute)
    
    Returns:
        Number of documents deleted
    """
    try:
        vector_store = VectorStore()
        deleted_count = vector_store.delete_by_source(source_file)
        
        logger.info(f"Deleted {deleted_count} documents from source: {source_file}")
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} documents from {source_file}",
            "deleted_count": deleted_count,
            "source_file": source_file
        }
    
    except Exception as e:
        logger.error(f"Failed to delete documents by source: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete documents: {str(e)}"
        )