"""
Script to convert HuggingFace CLIP model to GGUF format for clip-cpp

This script:
1. Clones the clip.cpp repository
2. Converts the existing HuggingFace CLIP model to GGUF format
3. Places the GGUF file in the correct location for the backend

Usage:
    python scripts/convert_clip_to_gguf.py
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

# Paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
DATA_DIR = BACKEND_DIR.parent / "data"
MODELS_DIR = DATA_DIR / "models"
CLIP_HF_DIR = MODELS_DIR / "clip-vit-base-patch32" / "models--openai--clip-vit-base-patch32" / "snapshots" / "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"
CLIP_GGUF_DIR = MODELS_DIR / "clip"
CLIP_CPP_DIR = BACKEND_DIR / "clip.cpp"

def download_preconverted_gguf():
    """Download pre-converted CLIP GGUF model from HuggingFace"""
    print("\n🔄 Downloading pre-converted CLIP GGUF model from HuggingFace...")
    
    try:
        from huggingface_hub import hf_hub_download
        
        # Download from the correct repo with pre-converted CLIP GGUF
        print("   Repository: mys/ggml_CLIP-ViT-B-32")
        print("   File: ggml-model-f16.gguf")
        
        gguf_path = hf_hub_download(
            repo_id="mys/ggml_CLIP-ViT-B-32",
            filename="ggml-model-f16.gguf",
            cache_dir=str(MODELS_DIR / "cache")
        )
        
        # Copy to expected location and rename
        final_path = CLIP_GGUF_DIR / "clip-vit-base-patch32.gguf"
        shutil.copy(gguf_path, final_path)
        
        file_size = final_path.stat().st_size / (1024 * 1024)  # Convert to MB
        print(f"\n✅ Downloaded pre-converted CLIP GGUF model")
        print(f"   Location: {final_path}")
        print(f"   Size: {file_size:.2f} MB")
        
        return True
    except Exception as e:
        print(f"\n⚠️  Download failed: {e}")
        print(f"\n📥 Manual Download Instructions:")
        print(f"   1. Go to: https://huggingface.co/mys/ggml_CLIP-ViT-B-32")
        print(f"   2. Download: ggml-model-f16.gguf")
        print(f"   3. Rename to: clip-vit-base-patch32.gguf")
        print(f"   4. Place in: {CLIP_GGUF_DIR}")
        return False

def main():
    print("=" * 80)
    print("CLIP Model Conversion to GGUF")
    print("=" * 80)
    
    # Try downloading pre-converted model first
    if download_preconverted_gguf():
        print("\n" + "=" * 80)
        print("✅ CLIP GGUF Model Ready!")
        print("=" * 80)
        return
    
    # Step 1: Check if HuggingFace CLIP model exists
    if not CLIP_HF_DIR.exists():
        print(f"\n❌ ERROR: HuggingFace CLIP model not found at {CLIP_HF_DIR}")
        print("Please download the model first using:")
        print("  python scripts/setup_models.py")
        sys.exit(1)
    
    print(f"\n✅ Found HuggingFace CLIP model at {CLIP_HF_DIR}")
    
    # Step 2: Clone clip.cpp repository if not already cloned
    if not CLIP_CPP_DIR.exists():
        print(f"\n📥 Cloning clip.cpp repository...")
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/monatis/clip.cpp.git", str(CLIP_CPP_DIR)],
                check=True,
                cwd=str(BACKEND_DIR)
            )
            print("✅ clip.cpp repository cloned successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ ERROR: Failed to clone clip.cpp repository: {e}")
            sys.exit(1)
    else:
        print(f"\n✅ clip.cpp repository already exists at {CLIP_CPP_DIR}")
    
    # Step 3: Create output directory
    CLIP_GGUF_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n✅ Output directory created: {CLIP_GGUF_DIR}")
    
    # Step 4: Convert HuggingFace model to GGUF
    print(f"\n🔄 Converting CLIP model to GGUF format...")
    print(f"   Source: {CLIP_HF_DIR}")
    print(f"   Target: {CLIP_GGUF_DIR}")
    
    conversion_script = CLIP_CPP_DIR / "models" / "convert_hf_to_gguf.py"
    
    if not conversion_script.exists():
        print(f"❌ ERROR: Conversion script not found at {conversion_script}")
        sys.exit(1)
    
    try:
        # Run conversion script (corrected arguments)
        result = subprocess.run(
            [
                sys.executable,
                str(conversion_script),
                "-m", str(CLIP_HF_DIR),
                "-o", str(CLIP_GGUF_DIR)
            ],
            check=True,
            cwd=str(CLIP_CPP_DIR),
            capture_output=True,
            text=True
        )
        
        print("\n✅ Conversion successful!")
        print(result.stdout)
        
        # Verify the GGUF file was created
        gguf_file = CLIP_GGUF_DIR / "clip-vit-base-patch32.gguf"
        if gguf_file.exists():
            file_size = gguf_file.stat().st_size / (1024 * 1024)  # Convert to MB
            print(f"\n✅ GGUF file created: {gguf_file}")
            print(f"   Size: {file_size:.2f} MB")
        else:
            print(f"\n⚠️  Warning: Expected GGUF file not found at {gguf_file}")
            print(f"   Checking for alternative file names...")
            gguf_files = list(CLIP_GGUF_DIR.glob("*.gguf"))
            if gguf_files:
                print(f"   Found: {[f.name for f in gguf_files]}")
                # Rename the first GGUF file to the expected name
                shutil.move(str(gguf_files[0]), str(gguf_file))
                print(f"   Renamed to: {gguf_file.name}")
            else:
                print(f"   ❌ No GGUF files found in {CLIP_GGUF_DIR}")
                sys.exit(1)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: Conversion failed")
        print(f"   Return code: {e.returncode}")
        print(f"   STDOUT: {e.stdout}")
        print(f"   STDERR: {e.stderr}")
        sys.exit(1)
    
    # Step 5: Cleanup (optional)
    print(f"\n🧹 Cleanup options:")
    print(f"   - Keep clip.cpp directory: {CLIP_CPP_DIR}")
    print(f"   - Keep HuggingFace model: {CLIP_HF_DIR}")
    print(f"\n💡 You can delete the clip.cpp directory if you don't need it anymore:")
    print(f"   shutil.rmtree('{CLIP_CPP_DIR}')")
    
    print("\n" + "=" * 80)
    print("✅ CLIP GGUF Conversion Complete!")
    print("=" * 80)
    print(f"\n📍 GGUF Model Location: {CLIP_GGUF_DIR / 'clip-vit-base-patch32.gguf'}")
    print(f"\n🚀 Next steps:")
    print(f"   1. Install clip-cpp: pip install clip-cpp")
    print(f"   2. Set CMAKE_ARGS for CUDA: set CMAKE_ARGS=\"-DGGML_CUDA=on\"")
    print(f"   3. Reinstall with CUDA: pip install clip-cpp --force-reinstall --no-cache-dir")
    print(f"   4. Start backend: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
