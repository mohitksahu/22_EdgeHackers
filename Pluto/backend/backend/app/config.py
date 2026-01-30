"""
Configuration settings for the Multimodal RAG System
"""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # =======================
    # API Keys
    # =======================
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    twilio_account_sid: str = Field("", env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field("", env="TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number: str = Field("", env="TWILIO_WHATSAPP_NUMBER")
    whatsapp_recipient_number: str = Field("", env="WHATSAPP_RECIPIENT_NUMBER")
    langsmith_api_key: str = Field("", env="LANGSMITH_API_KEY")
    langsmith_project_name: str = Field(
        "multimodal-rag-system", env="LANGSMITH_PROJECT_NAME"
    )

    # =======================
    # Application Metadata
    # =======================
    app_name: str = Field("Multimodal RAG System", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(True, env="DEBUG")
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")

    # =======================
    # Paths (derived, not env-driven)
    # =======================
    base_path: Path = Path(__file__).parent.parent.parent

    # =======================
    # LLM Configuration (llama.cpp)
    # =======================
    llm_backend: str = Field("llama_cpp", env="LLM_BACKEND")

    llama_cpp_n_gpu_layers: int = Field(-1, env="LLAMA_CPP_N_GPU_LAYERS")
    llama_cpp_main_gpu: int = Field(0, env="LLAMA_CPP_MAIN_GPU")
    llama_cpp_n_ctx: int = Field(4096, env="LLAMA_CPP_N_CTX")
    llama_cpp_n_batch: int = Field(512, env="LLAMA_CPP_N_BATCH")
    llama_cpp_n_threads: int = Field(8, env="LLAMA_CPP_N_THREADS")
    temperature: float = Field(0.1, env="TEMPERATURE")
    max_tokens: int = Field(2048, env="MAX_TOKENS")

    # =======================
    # Audio (Whisper)
    # =======================
    whisper_model_name: str = Field("base", env="WHISPER_MODEL_NAME")

    # =======================
    # Vector Store
    # =======================
    collection_name: str = Field("multimodal_documents", env="COLLECTION_NAME")
    embedding_dimension: int = Field(512, env="EMBEDDING_DIMENSION")

    # =======================
    # Retrieval
    # =======================
    max_retrieval_results: int = Field(10, env="MAX_RETRIEVAL_RESULTS")
    similarity_threshold: float = Field(0.2, env="SIMILARITY_THRESHOLD")
    reranking_enabled: bool = Field(True, env="RERANKING_ENABLED")

    # =======================
    # Uploads
    # =======================
    max_upload_size: int = Field(100_000_000, env="MAX_UPLOAD_SIZE")

    # IMPORTANT: List should NOT come from env directly
    allowed_extensions: List[str] = [
        "pdf", "doc", "docx", "txt",
        "jpg", "jpeg", "png",
        "mp3", "wav", "flac",
    ]

    # =======================
    # Notifications
    # =======================
    notification_enabled: bool = Field(True, env="NOTIFICATION_ENABLED")
    notification_conflict_threshold: float = Field(0.3, env="NOTIFICATION_CONFLICT_THRESHOLD")
    notification_uncertainty_threshold: float = Field(0.5, env="NOTIFICATION_UNCERTAINTY_THRESHOLD")

    # =======================
    # Logging
    # =======================
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False
        protected_namespaces = ()
        extra = "allow"

    # =======================
    # Derived Paths
    # =======================
    @property
    def data_dir(self) -> Path:
        return self.base_path / "data"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    @property
    def vectorstore_dir(self) -> Path:
        return self.data_dir / "vectorstore"

    @property
    def chromadb_dir(self) -> Path:
        return self.vectorstore_dir / "chromadb"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def log_file_path(self) -> Path:
        return self.logs_dir / "application" / "app.log"

    # =======================
    # Directory Bootstrap
    # =======================
    def ensure_directories(self) -> None:
        directories = [
            self.models_dir,
            self.vectorstore_dir,
            self.chromadb_dir,
            self.uploads_dir / "text",
            self.uploads_dir / "images",
            self.uploads_dir / "audio",
            self.uploads_dir / "processed",
            self.logs_dir / "application",
            self.logs_dir / "errors",
            self.cache_dir / "embeddings",
            self.cache_dir / "ocr_results",
            self.cache_dir / "transcriptions",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Singleton
settings = Settings()
settings.ensure_directories()
