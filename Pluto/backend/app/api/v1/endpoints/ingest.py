"""
Ingestion API endpoints (SCOPE-AWARE)
"""
import logging
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Header,
)

from app.ingestion.orchestrator import IngestionOrchestrator
from app.ingestion.validators.file_validator import FileValidator
from app.ingestion.metadata.extractor import MetadataExtractor
from app.core.scope_registry import set_last_scope
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
ingestion_orchestrator = IngestionOrchestrator()
metadata_extractor = MetadataExtractor()


@router.post("/file", response_model=Dict[str, Any])
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form("default_user"),
    chunking_strategy: str = Form("character"),
    chunk_size: int = Form(235),
    chunk_overlap: int = Form(30),
    x_scope_id: str | None = Header(default=None, alias="X-Scope-Id"),
) -> Dict[str, Any]:
    """
    Ingest a single file (scope isolated)
    """

    try:
        scope_id = "single-doc-scope"  # Fixed scope for single-document mode
        logger.info(f"[SCOPE] Using fixed scope for single-document mode: {scope_id}")

        # -------------------------------
        # Resolve upload directory
        # -------------------------------
        suffix = file.filename.lower().split(".")[-1]

        if suffix in ["pdf", "doc", "docx", "txt"]:
            upload_dir = settings.uploads_dir / "text"
        elif suffix in ["jpg", "jpeg", "png"]:
            upload_dir = settings.uploads_dir / "images"
        elif suffix in ["mp3", "wav", "flac"]:
            upload_dir = settings.uploads_dir / "audio"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / file.filename

        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())

        # -------------------------------
        # Validate
        # -------------------------------
        validator = FileValidator()
        if not validator.validate(temp_path):
            temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(validator.errors))

        # -------------------------------
        # Ingest
        # -------------------------------
        result = ingestion_orchestrator.ingest_and_store(
            file_path=temp_path,
            scope_id=scope_id,
            chunking_strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        result["filename"] = file.filename
        result["scope_id"] = scope_id

        # Register this as the active scope for the user
        set_last_scope(user_id, scope_id)

        background_tasks.add_task(temp_path.unlink, missing_ok=True)

        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return result

    except Exception as e:
        logger.exception("File ingestion failed")
        raise HTTPException(status_code=500, detail=str(e))
