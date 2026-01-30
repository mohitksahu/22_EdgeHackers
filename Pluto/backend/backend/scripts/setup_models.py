"""
Model Setup Script for PLUTO
Downloads models from Hugging Face into data/models/
- LLaMA 3.1 8B (Q4_K_M): unsloth/Meta-Llama-3.1-8B-Instruct-GGUF
- CLIP: openai/clip-vit-base-patch32
- Whisper: openai/whisper-base
"""
import os
from pathlib import Path
from huggingface_hub import hf_hub_download


import sys
# Save all models directly in the root data/models folder (f:/Pluto/data/models)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "data" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def download_llama():
    llama_filename = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
    llama_file = MODEL_DIR / llama_filename
    if llama_file.exists():
        print(f"Llama model already exists at {llama_file}, skipping download.")
        return
    print("Downloading Llama 3.2 1B GGUF model (Q4_K_M)...")
    llama_path = hf_hub_download(
        repo_id="bartowski/Llama-3.2-1B-Instruct-GGUF",
        filename=llama_filename,
        cache_dir=MODEL_DIR
    )
    print(f"Downloaded Llama model to {llama_path}")

def download_clip():
    print("Downloading CLIP (FastEmbed) ONNX models from Qdrant...")
    # Download CLIP text encoder
    clip_text_file = MODEL_DIR / "clip-ViT-B-32-text.onnx"
    if not clip_text_file.exists():
        clip_text = hf_hub_download(
            repo_id="Qdrant/clip-ViT-B-32-text",
            filename="model.onnx",
            cache_dir=MODEL_DIR
        )
        os.rename(clip_text, clip_text_file)
        print(f"Downloaded CLIP text encoder to {clip_text_file}")
    else:
        print(f"CLIP text encoder already exists at {clip_text_file}, skipping download.")
    # Download CLIP vision encoder
    clip_vision_file = MODEL_DIR / "clip-ViT-B-32-vision.onnx"
    if not clip_vision_file.exists():
        clip_vision = hf_hub_download(
            repo_id="Qdrant/clip-ViT-B-32-vision",
            filename="model.onnx",
            cache_dir=MODEL_DIR
        )
        os.rename(clip_vision, clip_vision_file)
        print(f"Downloaded CLIP vision encoder to {clip_vision_file}")
    else:
        print(f"CLIP vision encoder already exists at {clip_vision_file}, skipping download.")

def download_whisper():
    print("Downloading Faster-Whisper (CTranslate2) model files...")
    for fname in ["model.bin", "vocabulary.txt", "tokenizer.json", "config.json"]:
        whisper_file = MODEL_DIR / fname
        if whisper_file.exists():
            print(f"Whisper file already exists at {whisper_file}, skipping download.")
            continue
        file_path = hf_hub_download(
            repo_id="Systran/faster-whisper-base",
            filename=fname,
            cache_dir=MODEL_DIR
        )
        print(f"Downloaded Whisper file: {file_path}")

def main():
    download_llama()
    download_clip()
    download_whisper()
    print("All models downloaded.")

if __name__ == "__main__":
    main()
