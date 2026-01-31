import os
import logging
import warnings
import shutil

# Suppress warnings
os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["WHISPER_LOG_LEVEL"] = "ERROR"
logging.getLogger("onnxruntime").setLevel(logging.ERROR)
logging.getLogger("fastembed").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
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
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings

console = Console()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Configure logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
    )
    rich_handler.setLevel(getattr(logging, settings.log_level))
    
    file_handler = logging.FileHandler(settings.log_file_path)
    file_handler.setLevel(getattr(logging, settings.log_level))
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    root_logger.addHandler(rich_handler)
    root_logger.addHandler(file_handler)
    
    console.print("\n[bold blue]🚀 Starting Multimodal RAG System...[/bold blue]\n")
    
    # Validate GPU
    console.print("[yellow]⚡ Validating GPU availability...[/yellow]")
    try:
        from app.utils.gpu_check import validate_gpu_availability, get_gpu_info
        validate_gpu_availability()
        gpu_info = get_gpu_info()
        console.print(f"[green][OK] Hardware: {gpu_info['device']} ({', '.join(gpu_info['engines'])})[/green]")
    except Exception as e:
        console.print(f"[yellow][WARN] GPU check: {e}[/yellow]")
        gpu_info = {'device': 'cpu', 'engines': ['cpu']}
    
    # System info table
    table = Table(title="System Configuration")
    table.add_column("Component", style="cyan")
    table.add_column("Status/Value", style="magenta")
    table.add_row("Version", settings.app_version)
    table.add_row("Debug Mode", str(settings.debug))
    table.add_row("Hardware", gpu_info.get('device', 'cpu'))
    table.add_row("Qdrant Host", f"{settings.qdrant_host}:{settings.qdrant_port}")
    table.add_row("Models Path", str(settings.models_dir))
    console.print(table)
    
    # Warmup models
    console.print("\n[yellow]🔥 Warming up models...[/yellow]")
    try:
        # 1. CLIP embeddings
        from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
        console.print("[dim]   • Initializing CLIP...[/dim]")
        embedder = MultimodalEmbedder()
        test_embed = embedder.encode_text("test")
        console.print(f"[dim]   • CLIP ready: {len(test_embed)}D vectors[/dim]")
        
        # 2. Whisper (lazy load via property access)
        from app.ingestion.processors.audio_processor import AudioProcessor
        console.print("[dim]   • Initializing Whisper...[/dim]")
        audio_proc = AudioProcessor()
        _ = audio_proc.whisper_model  # Triggers lazy load
        console.print("[dim]   • Whisper ready[/dim]")
        
        # 3. Ollama LLM
        from app.reasoning.llm.ollama_reasoner import OllamaReasoner
        console.print("[dim]   • Initializing Ollama LLM...[/dim]")
        reasoner = OllamaReasoner()
        console.print(f"[dim]   • Ollama ready: {settings.ollama_model}[/dim]")
        
        # 4. Check Ollama Vision Models
        console.print("[dim]   • Checking vision models...[/dim]")
        try:
            import requests
            response = requests.get(f"{settings.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                vision_models = ['llava', 'llava:7b', 'llava:latest', 'bakllava', 'bakllava:latest', 'llama3.2-vision', 'llama3.2-vision:latest']
                available_vision = [m for m in models if any(v in m for v in ['llava', 'bakllava', 'vision'])]
                
                if available_vision:
                    console.print(f"[dim]   • Vision models: {', '.join(available_vision)}[/dim]")
                else:
                    console.print("[yellow]   • Vision models: None found (image descriptions will use fallback)[/yellow]")
                    console.print("[yellow]     Run: ollama pull llava[/yellow]")
                
                # Show all available models
                other_models = [m for m in models if m not in available_vision and settings.ollama_model not in m]
                if other_models:
                    console.print(f"[dim]   • Other Ollama models: {', '.join(other_models[:5])}{'...' if len(other_models) > 5 else ''}[/dim]")
            else:
                console.print("[yellow]   • Vision models: Could not check[/yellow]")
        except Exception as e:
            console.print(f"[yellow]   • Vision models: Check failed ({e})[/yellow]")
        
        console.print("[green][OK] All models ready![/green]")
        
    except Exception as e:
        console.print(f"[yellow][WARN] Warmup: {e}[/yellow]")
    
    # Check vector store
    console.print("\n[yellow]📚 Checking knowledge base...[/yellow]")
    try:
        from app.storage.vector_store import VectorStore
        vs = VectorStore()
        info = vs.get_collection_info()
        points = info.get('points_count', 0)
        if points > 0:
            console.print(f"[green][OK] Knowledge base: {points} vectors indexed[/green]")
        else:
            console.print("[yellow][INFO] Knowledge base empty - upload documents to begin[/yellow]")
    except Exception as e:
        console.print(f"[yellow][WARN] Vector store: {e}[/yellow]")
    
    root_logger.info(f"Application version: {settings.app_version}")
    console.print("\n[green][OK] Application startup complete![/green]\n")
    
    yield
    
    console.print("\n[yellow]⏹️  Shutting down...[/yellow]")
    root_logger.info("Shutting down Multimodal RAG System...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multimodal RAG System with CLIP embeddings",
    lifespan=lifespan,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZIP compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


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
    logger.error(f"Error in {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
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
    )