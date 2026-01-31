"""
Ingestion API Endpoints - Fixed parameter handling
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config import settings
from app.core.logging_config import get_safe_logger
from app.ingestion.orchestrator import IngestionOrchestrator
from app.ingestion.validators.file_validator import FileValidator

logger = get_safe_logger(__name__)
router = APIRouter()

# Initialize components
file_validator = FileValidator()
ingestion_orchestrator = IngestionOrchestrator()


class IngestionResponse(BaseModel):
    status: str
    message: str
    file_name: str
    session_id: str
    chunks: int = 0
    indexed: int = 0
    topic: Optional[str] = None
    concepts: Optional[List[str]] = None


class IngestionStatusResponse(BaseModel):
    status: str
    message: str
    progress: float = 0.0


# Track background task status
_ingestion_status = {}


@router.post("/file", response_model=IngestionResponse)
async def ingest_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    chunking_strategy: Optional[str] = Form("semantic"),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
):
    """
    Ingest a single file into the knowledge base
    
    Args:
        file: The file to upload
        session_id: Session identifier for organizing documents
        chunking_strategy: Strategy for chunking ('semantic', 'fixed', 'sentence')
        chunk_size: Optional custom chunk size
        chunk_overlap: Optional custom overlap
    """
    logger.info(f"Ingesting file: {file.filename}")
    
    # Validate file
    is_valid, error_message = file_validator.validate_upload(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Save uploaded file
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename to avoid conflicts
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = upload_dir / unique_filename
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"[OK] File saved to: {file_path}")
        
        # Build metadata
        metadata = {
            "original_filename": file.filename,
            "chunking_strategy": chunking_strategy,
        }
        
        if chunk_size:
            metadata["chunk_size"] = chunk_size
        if chunk_overlap:
            metadata["chunk_overlap"] = chunk_overlap
        
        # Run ingestion
        result = ingestion_orchestrator.ingest_and_store(
            file_path=str(file_path),
            session_id=session_id,
            metadata=metadata
        )
        
        return IngestionResponse(
            status=result.get("status", "success"),
            message=result.get("message", f"Processed {file.filename}"),
            file_name=file.filename,
            session_id=session_id,
            chunks=result.get("chunks", 0),
            indexed=result.get("indexed", 0),
            topic=result.get("topic"),
            concepts=result.get("concepts")
        )
        
    except Exception as e:
        logger.error(f"Failed to ingest file {file.filename}: {e}")
        # Clean up on failure
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file/async", response_model=IngestionStatusResponse)
async def ingest_file_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    chunking_strategy: Optional[str] = Form("semantic"),
):
    """
    Ingest a file asynchronously (for large files)
    Returns immediately and processes in background
    """
    logger.info(f"[ASYNC] Queuing file for ingestion: {file.filename}")
    
    # Validate file
    is_valid, error_message = file_validator.validate_upload(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Save uploaded file
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = upload_dir / unique_filename
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Initialize status
        _ingestion_status[task_id] = {
            "status": "queued",
            "progress": 0.0,
            "message": "File queued for processing"
        }
        
        # Add to background tasks
        background_tasks.add_task(
            _process_file_background,
            task_id=task_id,
            file_path=str(file_path),
            session_id=session_id,
            metadata={"chunking_strategy": chunking_strategy}
        )
        
        return IngestionStatusResponse(
            status="queued",
            message=f"File {file.filename} queued. Task ID: {task_id}",
            progress=0.0
        )
        
    except Exception as e:
        logger.error(f"Failed to queue file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_file_background(
    task_id: str,
    file_path: str,
    session_id: str,
    metadata: dict
):
    """Background task for file processing"""
    try:
        _ingestion_status[task_id] = {
            "status": "processing",
            "progress": 0.1,
            "message": "Starting processing..."
        }
        
        result = ingestion_orchestrator.ingest_and_store(
            file_path=file_path,
            session_id=session_id,
            metadata=metadata
        )
        
        _ingestion_status[task_id] = {
            "status": "completed",
            "progress": 1.0,
            "message": f"Completed: {result.get('chunks', 0)} chunks indexed"
        }
        
    except Exception as e:
        logger.error(f"Background ingestion failed: {e}")
        _ingestion_status[task_id] = {
            "status": "failed",
            "progress": 0.0,
            "message": str(e)
        }


@router.get("/status/{task_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(task_id: str):
    """Get status of async ingestion task"""
    if task_id not in _ingestion_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = _ingestion_status[task_id]
    return IngestionStatusResponse(
        status=status["status"],
        message=status["message"],
        progress=status["progress"]
    )


@router.post("/batch")
async def ingest_batch(
    files: List[UploadFile] = File(...),
    session_id: str = Form(...),
):
    """Ingest multiple files"""
    results = []
    
    for file in files:
        try:
            # Process each file
            response = await ingest_file(
                file=file,
                session_id=session_id,
                chunking_strategy="semantic"
            )
            results.append({
                "file": file.filename,
                "status": "success",
                "chunks": response.chunks
            })
        except Exception as e:
            results.append({
                "file": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "status": "completed",
        "results": results,
        "total": len(files),
        "successful": sum(1 for r in results if r["status"] == "success")
    }


@router.delete("/session/{session_id}")
async def delete_session_documents(session_id: str):
    """Delete all documents for a session"""
    try:
        from app.storage.vector_store import VectorStore
        store = VectorStore()
        result = store.delete_by_session(session_id)
        return result
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))