"""
Llama Reasoner using llama-cpp-python with CUDA GPU offloading
Singleton pattern to prevent multiple model loads
"""
import logging
import os
import threading
from typing import List, Dict, Any, Optional
from llama_cpp import Llama
from app.config import settings

logger = logging.getLogger(__name__)

class LlamaReasoner:
    """Llama-3.2-1B-Instruct GGUF Reasoner with full GPU offloading (Singleton)"""
    
    _instance = None
    _llm = None
    _lock = threading.Lock()  # Thread-safe singleton
    
    def __new__(cls, model_path: Optional[str] = None):
        """Thread-safe singleton pattern: only one instance of LlamaReasoner"""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super(LlamaReasoner, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: Optional[str] = None):
        # Skip if already initialized
        if self._initialized:
            return
            
        # Use the exact absolute path to the GGUF model file in the snapshot folder
        model_path = model_path or str(settings.models_dir / "models--bartowski--Llama-3.2-1B-Instruct-GGUF" / "snapshots" / "067b946cf014b7c697f3654f621d577a3e3afd1c" / "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
        
        self.model_path = model_path
        self.n_ctx = settings.llama_cpp_n_ctx
        self.n_threads = settings.llama_cpp_n_threads
        self.n_gpu_layers = settings.llama_cpp_n_gpu_layers
        self.n_batch = settings.llama_cpp_n_batch
        self.main_gpu = settings.llama_cpp_main_gpu
        self.verbose = False  # Set to False to hide metadata dumps and control token warnings
        
        # Load model only once
        if LlamaReasoner._llm is None:
            with LlamaReasoner._lock:
                # Double-check locking for model load
                if LlamaReasoner._llm is None:
                    self._load_model()
        else:
            logger.info("Using existing Llama model instance (singleton)")
            
        self._initialized = True

    def _load_model(self):
        logger.info(f"Loading Llama model (singleton): {self.model_path}")
        
        # Verify file exists before loading
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Llama model file not found: {self.model_path}")
        
        LlamaReasoner._llm = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_gpu_layers=self.n_gpu_layers,
            n_batch=self.n_batch,
            main_gpu=self.main_gpu,
            verbose=self.verbose
        )
        # Check GPU offloading status
        actual_gpu_layers = getattr(LlamaReasoner._llm, 'n_gpu_layers', 0)
        if actual_gpu_layers > 0:
            logger.info(f"Llama model loaded with {actual_gpu_layers} layers on GPU.")
        else:
            logger.warning("Llama model loaded on CPU. GPU offloading not available.")
    
    @property
    def llm(self):
        """Access the shared LLM instance"""
        return LlamaReasoner._llm

    def generate_response(self, system_prompt: str, user_prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self.llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response["choices"][0]["message"]["content"].strip()

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7, stop_sequences: list = None) -> str:
        """Generates a response from the Llama model (alias for compatibility)."""
        try:
            # Using the chat format for Llama 3.2 Instruct
            completion_params = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Add stop sequences if provided
            if stop_sequences:
                completion_params["stop"] = stop_sequences
            
            response = self.llm.create_chat_completion(**completion_params)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM Generation Error: {e}")
            return "I encountered an error generating the final answer."

    # Add any evidence/citation/refusal logic as needed, but do not change prompt semantics.
