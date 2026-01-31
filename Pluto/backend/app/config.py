"""
Global Configuration for Multimodal RAG System
Optimized for RTX 3050 6GB VRAM with Llama 3.2 1B
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


def get_path(env_var: str, default: str) -> Path:
    """Get path from environment variable or default"""
    return Path(os.getenv(env_var, default))


class Settings(BaseSettings):
    """Application settings with VRAM-optimized defaults for RTX 3050 6GB"""

    # ===========================================
    # APPLICATION SETTINGS
    # ===========================================
    app_name: str = "Multimodal RAG System"
    app_version: str = "2.0.0"
    debug: bool = Field(default=True, env="DEBUG")
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # ===========================================
    # PATH SETTINGS (Docker compatible)
    # ===========================================
    base_dir: Path = Field(default_factory=lambda: get_path("BASE_DIR", "/app"))
    data_dir: Path = Field(default_factory=lambda: get_path("DATA_DIR", "/app/data"))
    models_dir: Path = Field(default_factory=lambda: get_path("MODELS_DIR", "/app/data/models"))
    upload_dir: Path = Field(default_factory=lambda: get_path("UPLOAD_DIR", "/app/data/uploads"))
    log_file_path: Path = Field(default_factory=lambda: get_path("LOG_FILE_PATH", "/app/data/logs/app.log"))
    chat_history_dir: Path = Field(default_factory=lambda: get_path("CHAT_HISTORY_DIR", "/app/data/chat_history"))

    # ===========================================
    # GPU / VRAM BUDGET (RTX 3050 6GB)
    # ===========================================
    total_vram_gb: float = 6.0
    vram_buffer_gb: float = 0.5  # Reserve for OS/display

    # VRAM Allocation Strategy with Llama 3.2 1B:
    # - Ollama LLM (1B): ~1.5GB
    # - CLIP Embeddings: ~0.8GB
    # - Whisper (base): ~0.5GB
    # - Qdrant/Other: ~0.5GB
    # - Buffer: ~0.5GB
    # Total: ~3.8GB (plenty of headroom!)

    ollama_vram_gb: float = 1.5
    clip_vram_gb: float = 0.8
    whisper_vram_gb: float = 0.5

    # ===========================================
    # OLLAMA SETTINGS - Using Llama 3.2 1B
    # ===========================================
    ollama_host: str = "http://localhost:11434"
    
    # IMPORTANT: Using 1B model for all tasks
    ollama_model: str = "llama3.2:1b"
    ollama_embedding_model: str = "nomic-embed-text"  # Optional
    
    ollama_timeout: int = 120
    ollama_num_ctx: int = 4096  # Context window (1B supports up to 128k but 4k is efficient)
    ollama_num_gpu: int = 99  # Layers to offload to GPU (99 = all)
    ollama_num_thread: int = 4
    ollama_temperature: float = 0.1
    ollama_top_p: float = 0.9
    ollama_top_k: int = 40
    ollama_repeat_penalty: float = 1.1

    # Fallback llama_cpp settings (not used with Ollama)
    llama_cpp_n_ctx: int = 2048
    llama_cpp_n_threads: int = 4
    llama_cpp_n_gpu_layers: int = 99
    llama_cpp_n_batch: int = 512
    llama_cpp_main_gpu: int = 0

    # ===========================================
    # EMBEDDING SETTINGS (FastEmbed CLIP)
    # ===========================================
    embedding_model: str = "Qdrant/clip-ViT-B-32-text"
    embedding_dimension: int = 512
    image_embedding_model: str = "Qdrant/clip-ViT-B-32-vision"
    embedding_batch_size: int = 32
    embedding_max_length: int = 77  # CLIP token limit

    # ===========================================
    # WHISPER SETTINGS (Audio Transcription)
    # ===========================================
    whisper_model: str = "base"  # tiny, base, small, medium
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"  # float16 for GPU
    whisper_beam_size: int = 5
    whisper_language: str = "en"

    # ===========================================
    # QDRANT SETTINGS
    # ===========================================
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    collection_name: str = "pluto_multimodal"
    qdrant_prefer_grpc: bool = False

    # ===========================================
    # RETRIEVAL SETTINGS
    # ===========================================
    # Vector Search
    similarity_threshold: float = 0.35
    default_top_k: int = 10
    max_top_k: int = 50

    # BM25 Settings
    bm25_enabled: bool = True
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    bm25_weight: float = 0.3

    # MMR Settings
    mmr_enabled: bool = True
    mmr_lambda: float = 0.7
    mmr_fetch_k: int = 20

    # Multi-Query Settings
    multi_query_enabled: bool = True
    multi_query_count: int = 3

    # Hybrid Search Weights
    dense_weight: float = 0.5
    sparse_weight: float = 0.3
    rerank_weight: float = 0.2

    # Reranking
    reranking_enabled: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_k: int = 5

    # ===========================================
    # MULTI-AGENT SETTINGS - All use 1B model
    # ===========================================
    agent_supervisor_model: str = "llama3.2:1b"
    agent_worker_model: str = "llama3.2:1b"
    agent_max_iterations: int = 5
    agent_timeout: int = 60

    # Agent Types
    enable_retrieval_agent: bool = True
    enable_reasoning_agent: bool = True
    enable_validation_agent: bool = True
    enable_response_agent: bool = True

    # ===========================================
    # CHUNKING SETTINGS
    # ===========================================
    chunk_size: int = 235
    chunk_overlap: int = 30
    min_chunk_size: int = 50

    # ===========================================
    # EVIDENCE & REASONING
    # ===========================================
    confidence_threshold: float = 0.5
    refusal_threshold: float = 0.3
    max_evidence_pieces: int = 5
    conflict_detection_enabled: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.data_dir,
            self.models_dir,
            self.upload_dir,
            self.upload_dir / "text",
            self.upload_dir / "images",
            self.upload_dir / "audio",
            self.upload_dir / "processed",
            self.log_file_path.parent,
            self.chat_history_dir,
            self.data_dir / "logs" / "retrieval",
            self.logs_dir / "application",
            self.logs_dir / "errors",
            self.logs_dir / "retrieval",
            self.cache_dir / "embeddings",
            self.cache_dir / "ocr_results",
            self.cache_dir / "transcriptions",
            self.vectorstore_dir,
            self.qdrant_storage_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_vram_allocation(self) -> dict:
        """Get current VRAM allocation strategy"""
        allocated = self.ollama_vram_gb + self.clip_vram_gb + self.whisper_vram_gb + self.vram_buffer_gb
        return {
            "total_vram_gb": self.total_vram_gb,
            "allocated": {
                "ollama_llm_1b": self.ollama_vram_gb,
                "clip_embeddings": self.clip_vram_gb,
                "whisper_base": self.whisper_vram_gb,
                "buffer": self.vram_buffer_gb,
            },
            "total_allocated": allocated,
            "available": self.total_vram_gb - allocated
        }

    def get_ollama_options(self) -> dict:
        """Get Ollama generation options"""
        return {
            "num_ctx": self.ollama_num_ctx,
            "num_gpu": self.ollama_num_gpu,
            "num_thread": self.ollama_num_thread,
            "temperature": self.ollama_temperature,
            "top_p": self.ollama_top_p,
            "top_k": self.ollama_top_k,
            "repeat_penalty": self.ollama_repeat_penalty,
        }


    @property
    def uploads_dir(self) -> Path:
        """Alias for upload_dir to match expected naming"""
        return self.upload_dir

    @property
    def vectorstore_dir(self) -> Path:
        return self.data_dir / "vectorstore"

    @property
    def qdrant_storage_dir(self) -> Path:
        return self.vectorstore_dir / "qdrant_storage"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"


# Global settings instance
settings = Settings()