#!/usr/bin/env python3
"""
Initialize PLUTO system
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 60)
    print("PLUTO SYSTEM INITIALIZATION")
    print("=" * 60)
    
    # Import after path setup
    from app.config import settings
    
    # Create directories
    settings.ensure_directories()
    print("[OK] Directories created")
    
    # Check Ollama
    print("\n" + "=" * 60)
    print("CHECKING OLLAMA")
    print("=" * 60)
    
    import requests
    try:
        response = requests.get(f"{settings.ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get('models', [])]
            print(f"[OK] Ollama running with models: {models}")
            
            if settings.ollama_model not in models:
                print(f"[WARN] Model {settings.ollama_model} not found")
                print(f"       Run: ollama pull {settings.ollama_model}")
        else:
            print(f"[FAIL] Ollama returned: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Cannot connect to Ollama: {e}")
        print("       Run: ollama serve")
    
    # Initialize Qdrant
    print("\n" + "=" * 60)
    print("INITIALIZING QDRANT")
    print("=" * 60)
    
    try:
        from app.storage.vector_store import VectorStore
        store = VectorStore()
        info = store.get_collection_info()
        print(f"[OK] Collection: {info.get('name', 'unknown')}")
        print(f"     Points: {info.get('points_count', 0)}")
        print(f"     Status: {info.get('status', 'unknown')}")
    except Exception as e:
        print(f"[FAIL] Qdrant error: {e}")
    
    print("\n" + "=" * 60)
    print("INITIALIZATION COMPLETE")
    print("=" * 60)
    print("\nStart the backend:")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")


if __name__ == "__main__":
    main()