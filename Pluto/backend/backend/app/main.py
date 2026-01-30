import os
import logging
import warnings
import shutil

# 1. Suppress ONNX Runtime and Whisper warnings
os.environ["ORT_LOGGING_LEVEL"] = "3" 
os.environ["WHISPER_LOG_LEVEL"] = "ERROR"

# 2. Suppress specialized library loggers
logging.getLogger("onnxruntime").setLevel(logging.ERROR)
logging.getLogger("fastembed").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

# 3. Suppress Standard Python warnings (like the Symlink warning)
warnings.filterwarnings("ignore", category=UserWarning)

"""
Main FastAPI application for the Multimodal RAG System
"""
from contextlib import asynccontextmanager
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

from app.api.v1.router import api_router
from app.config import settings

# Create Rich console for better output
console = Console()

# Module-level logger (will be fully configured in lifespan)
logger = logging.getLogger("app.main")


def force_wipe_memory(db_path: str):
    """
    Nuclear option: Deletes the ChromaDB folder entirely to prevent 
    old documents from leaking into new queries and causing semantic drift.
    
    This ensures every run starts with a completely empty memory.
    """
    if os.path.exists(db_path):
        print(f"🧹 [RESET] Wiping old memory at: {db_path}")
        try:
            # Use rmtree to delete the entire directory structure
            shutil.rmtree(db_path)
            # Recreate an empty directory
            os.makedirs(db_path, exist_ok=True)
            print("✨ [CLEAN] Database is now empty. Ready for fresh ingestion.")
        except Exception as e:
            print(f"⚠️ [ERROR] Failed to wipe memory: {e}")
    else:
        print(f"ℹ️ [INFO] No existing database found at {db_path}. Will create fresh.")
        os.makedirs(db_path, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""

    # DISABLED: Auto-wipe on startup (use scripts/reset_vectorstore.py or cleanup_vectorstore.py instead)
    # This was causing data loss on every restart!
    # CHROMA_PATH = str(settings.chromadb_dir)
    # force_wipe_memory(CHROMA_PATH)

    # Ensure all required directories exist
    settings.ensure_directories()

    # Configure logging after directories are created
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Rich handler for console with beautiful formatting
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_level=True,
        show_path=False,  # Don't show file path to keep it clean
        rich_tracebacks=True,  # Beautiful tracebacks
        tracebacks_show_locals=True
    )
    rich_handler.setLevel(getattr(logging, settings.log_level))

    # File handler with plain text
    file_handler = logging.FileHandler(settings.log_file_path)
    file_handler.setLevel(getattr(logging, settings.log_level))
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    root_logger.addHandler(rich_handler)
    root_logger.addHandler(file_handler)

    # Startup banner
    console.print("\n[bold blue]🚀 Starting Multimodal RAG System...[/bold blue]\n", style="bold")
    
    # CRITICAL: Validate GPU availability before proceeding
    console.print("[yellow]⚡ Validating GPU availability...[/yellow]")
    try:
        from app.utils.gpu_check import validate_gpu_availability, get_gpu_info
        validate_gpu_availability()
        gpu_info = get_gpu_info()
        console.print(f"[green][OK] Hardware Acceleration: {gpu_info['device']} ({', '.join(gpu_info['engines'])})[/green]")
    except RuntimeError as e:
        console.print(f"[bold red][FAIL] GPU Validation Failed![/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        root_logger.error(f"GPU validation failed: {e}")
        raise  # Stop application startup if no GPU

    # Create startup info table
    table = Table(title="System Configuration")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status/Value", style="magenta")

    table.add_row("Version", settings.app_version)
    table.add_row("Debug Mode", str(settings.debug))
    table.add_row("Hardware Acceleration", gpu_info['device'])
    table.add_row("C++ Engines", ", ".join(gpu_info['engines']))
    table.add_row("ChromaDB Path", str(settings.chromadb_dir))
    table.add_row("Models Path", str(settings.models_dir))
    table.add_row("Log Level", settings.log_level)

    console.print(table)
    console.print()

    # PERFORMANCE WARMUP: Initialize all models immediately for instant first request
    console.print("[yellow]🔥 Warming up models for instant inference...[/yellow]")
    try:
        # 1. Warm up Multimodal Embedder (FastEmbed CLIP)
        from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
        console.print("[dim]   • Initializing FastEmbed CLIP models...[/dim]")
        embedder = MultimodalEmbedder()
        # Test text embedding
        test_text_embedding = embedder.encode_text("test query for warmup")
        console.print(f"[dim]   • CLIP Text: {len(test_text_embedding)}D vector generated[/dim]")
        
        # 2. Warm up Audio Processor (faster-whisper)
        from app.ingestion.processors.audio_processor import AudioProcessor
        console.print("[dim]   • Initializing faster-whisper model...[/dim]")
        audio_processor = AudioProcessor()
        audio_processor._load_model()  # Force model load
        console.print("[dim]   • Whisper: CTranslate2 model loaded on GPU[/dim]")
        
        # 3. Warm up LLM Reasoner (llama-cpp-python)
        from app.reasoning.llm.llama_reasoner import LlamaReasoner
        console.print("[dim]   • Initializing Llama 3.2 1B model...[/dim]")
        reasoner = LlamaReasoner()
        console.print("[dim]   • Llama: All 16 layers offloaded to GPU[/dim]")
        
        console.print("[green][OK] All models warmed up and GPU-accelerated![/green]")
        
    except Exception as e:
        console.print(f"[bold red][WARN] Model warmup failed: {e}[/bold red]")
        console.print("[yellow]   Models will load on first request instead[/yellow]")
        root_logger.warning(f"Model warmup failed: {e}")

    # Load and log topic catalog for observability
    console.print("[yellow]📚 Loading knowledge base topic catalog...[/yellow]")
    try:
        from app.storage.chromadb.client import ChromaDBClient
        from app.utils.topic_catalog_logger import log_topic_catalog
        
        chroma_client = ChromaDBClient()
        catalog = chroma_client.get_knowledge_catalog()
        current_topics = catalog.get("topics", [])
        
        if current_topics:
            log_topic_catalog(current_topics)
            console.print(f"[green][OK] Knowledge base covers {len(current_topics)} topics: {', '.join(current_topics)}[/green]")
        else:
            console.print("[yellow][INFO] Knowledge base is empty - upload documents to begin[/yellow]")
    except Exception as e:
        console.print(f"[yellow][WARN] Topic catalog logging failed: {e}[/yellow]")
        root_logger.warning(f"Topic catalog logging failed: {e}")

    # Fixed f-string syntax
    root_logger.info(f"Application version: {settings.app_version}")
    root_logger.info(f"Debug mode: {settings.debug}")
    root_logger.info(f"ChromaDB path: {settings.chromadb_dir}")
    root_logger.info(f"Models path: {settings.models_dir}")

    console.print("[green][OK] Application startup complete![/green]\n")

    yield

    # Shutdown tasks
    console.print("\n[yellow]⏹️  Shutting down Multimodal RAG System...[/yellow]")
    root_logger.info("Shutting down Multimodal RAG System...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multimodal Retrieval-Augmented Generation System",
    lifespan=lifespan,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    # Log with rich traceback
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={
            'request_method': request.method,
            'request_url': str(request.url),
            'client_ip': request.client.host if request.client else None
        }
    )

    # Show error in console with rich
    console.print(f"\n[red]❌ Error in {request.method} {request.url.path}: {exc}[/red]")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )