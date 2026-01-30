#!/usr/bin/env python3
"""
Download Llama-3.2-1B-Instruct-Q4_K_M.gguf model
"""

import os
from pathlib import Path
from huggingface_hub import hf_hub_download

def main():
    model_dir = Path(__file__).parent.parent.parent / "data" / "models" / "llama"
    model_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading Llama-3.2-1B-Instruct-Q4_K_M.gguf...")
    model_path = hf_hub_download(
        repo_id="bartowski/Llama-3.2-1B-Instruct-GGUF",
        filename="Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        cache_dir=model_dir
    )
    print(f"Downloaded to: {model_path}")

if __name__ == "__main__":
    main()