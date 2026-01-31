#!/usr/bin/env python3
"""
Ollama Setup Script for PLUTO
Ensures Ollama is installed and required models are pulled
"""
import subprocess
import sys
import time
import requests


# Use only 1B model for RTX 3050 6GB
REQUIRED_MODELS = [
    "llama3.2:1b",      # Single model for all tasks (lower VRAM)
]

OLLAMA_HOST = "http://localhost:11434"


def check_ollama_running():
    """Check if Ollama server is running"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_ollama():
    """Attempt to start Ollama server"""
    print("Starting Ollama server...")
    try:
        # Try to start Ollama in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Wait for server to start
        for _ in range(30):
            time.sleep(1)
            if check_ollama_running():
                print("✅ Ollama server started successfully")
                return True
        print("⚠️  Ollama server did not start in time")
        return False
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first:")
        print("   https://ollama.ai/download")
        return False


def get_installed_models():
    """Get list of installed models"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code == 200:
            data = response.json()
            return [m['name'] for m in data.get('models', [])]
    except Exception as e:
        print(f"Error getting models: {e}")
    return []


def is_model_installed(model_name: str, installed_models: list) -> bool:
    """Check if exact model is installed"""
    # Check exact match
    if model_name in installed_models:
        return True
    # Check with :latest suffix
    if f"{model_name}:latest" in installed_models:
        return True
    # Check if installed has :latest and we're looking for base
    if model_name.endswith(":latest"):
        base_name = model_name.replace(":latest", "")
        if base_name in installed_models:
            return True
    return False


def pull_model(model_name: str):
    """Pull a model from Ollama registry"""
    print(f"Pulling model: {model_name}...")
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {model_name} pulled successfully")
            return True
        else:
            print(f"❌ Failed to pull {model_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error pulling {model_name}: {e}")
        return False


def test_model_inference(model_name: str) -> bool:
    """Test model inference"""
    print(f"\nTesting inference with {model_name}...")
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model_name,
                "prompt": "Say hello in one word:",
                "options": {
                    "num_predict": 10,
                    "temperature": 0.1
                },
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            generated = result.get('response', '').strip()
            print(f"✅ Model response: {generated[:50]}")
            return True
        else:
            print(f"❌ Inference failed with status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("⚠️  Inference timed out (model may still be loading)")
        return False
    except Exception as e:
        print(f"❌ Inference error: {e}")
        return False


def main():
    print("=" * 60)
    print("OLLAMA SETUP FOR PLUTO (Llama 3.2 1B)")
    print("=" * 60)
    
    # Check if Ollama is running
    if not check_ollama_running():
        print("Ollama is not running. Attempting to start...")
        if not start_ollama():
            print("\n❌ Could not start Ollama. Please start it manually:")
            print("   ollama serve")
            sys.exit(1)
    else:
        print("✅ Ollama server is running")
    
    # Get installed models
    installed = get_installed_models()
    print(f"\nCurrently installed models: {installed}")
    
    # Pull required models
    print("\nChecking required models...")
    for model in REQUIRED_MODELS:
        if is_model_installed(model, installed):
            print(f"✅ {model} is installed")
        else:
            print(f"📥 {model} not found, pulling...")
            if not pull_model(model):
                print(f"❌ Failed to pull {model}")
                sys.exit(1)
    
    # Verify GPU access with actual inference
    print("\n" + "=" * 60)
    print("VERIFYING GPU ACCESS & INFERENCE")
    print("=" * 60)
    
    model_to_test = REQUIRED_MODELS[0]
    if test_model_inference(model_to_test):
        print("\n✅ Ollama setup complete!")
    else:
        print("\n⚠️  Inference test had issues, but setup may still work")
        print("   Try running: ollama run llama3.2:1b")
    
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"Ollama Host: {OLLAMA_HOST}")
    print(f"Model: {REQUIRED_MODELS[0]}")
    print(f"VRAM Usage: ~1.5-2GB (fits RTX 3050 6GB)")
    print("\nYou can now start the PLUTO backend!")


if __name__ == "__main__":
    main()