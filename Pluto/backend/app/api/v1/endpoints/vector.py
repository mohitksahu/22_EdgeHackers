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
        logger.info("Starting vector store reset...")
        vector_store = VectorStore()
        deleted_count = vector_store.reset()
        logger.info(f"Vector store reset completed, deleted {deleted_count} documents")

        return {
            "status": "success",
            "message": f"Vector store has been reset. {deleted_count} embeddings and data have been deleted."
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
        
        # Get all documents to count by modality
        all_docs = vector_store.chroma_client.get_documents()
        
        # Initialize modality counts
        modality_counts = {
            "text": 0,
            "image": 0,
            "audio": 0
        }
        
        # Count documents by modality
        if all_docs and 'metadatas' in all_docs:
            for metadata in all_docs['metadatas']:
                modality = metadata.get('modality', 'unknown')
                if modality in modality_counts:
                    modality_counts[modality] += 1
                # Silently ignore unknown modalities
        
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
    
    This is useful when files were manually deleted but their vectors remain in ChromaDB.
    
    Returns:
        Number of orphaned documents deleted and list of cleaned files
    """
    try:
        vector_store = VectorStore()
        
        # Get all documents
        all_docs = vector_store.chroma_client.get_documents()
        
        if not all_docs or 'metadatas' not in all_docs or 'ids' not in all_docs:
            return {
                "status": "success",
                "message": "No documents found in vector store",
                "deleted_count": 0,
                "deleted_sources": []
            }
        
        # Track orphaned documents
        orphaned_ids = []
        orphaned_sources = set()
        checked_files = {}  # Cache file existence checks
        
        # Check each document's source file
        for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas']):
            source_file = metadata.get('source_file', '')
            
            if not source_file:
                # No source file metadata - consider orphaned
                orphaned_ids.append(doc_id)
                orphaned_sources.add('<unknown>')
                continue
            
            # Check if we've already verified this file
            if source_file not in checked_files:
                file_path = Path(source_file)
                checked_files[source_file] = file_path.exists()
            
            # If file doesn't exist, mark as orphaned
            if not checked_files[source_file]:
                orphaned_ids.append(doc_id)
                orphaned_sources.add(source_file)
        
        # Delete orphaned documents
        deleted_count = 0
        if orphaned_ids:
            logger.info(f"🧹 Found {len(orphaned_ids)} orphaned documents from {len(orphaned_sources)} sources")
            vector_store.chroma_client.delete_documents(ids=orphaned_ids)
            deleted_count = len(orphaned_ids)
            logger.info(f"✨ Cleaned up {deleted_count} orphaned documents")
        
        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} orphaned documents",
            "deleted_count": deleted_count,
            "deleted_sources": sorted(list(orphaned_sources)),
            "total_checked": len(all_docs['ids'])
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