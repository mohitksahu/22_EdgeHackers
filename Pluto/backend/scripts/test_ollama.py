#!/usr/bin/env python3
"""Quick test for Ollama with Llama 3.2 1B"""
import requests
import json

OLLAMA_HOST = "http://localhost:11434"
MODEL = "llama3.2:1b"

def test_generate():
    """Test basic generation"""
    print(f"Testing {MODEL} generation...")
    
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL,
            "prompt": "What is 2 + 2? Answer in one word:",
            "options": {
                "num_predict": 20,
                "temperature": 0.1
            },
            "stream": False
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data.get('response', 'No response')}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return False

def test_chat():
    """Test chat completion"""
    print(f"\nTesting {MODEL} chat...")
    
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Be brief."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            "options": {
                "num_predict": 50,
                "temperature": 0.1
            },
            "stream": False
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        content = data.get('message', {}).get('content', 'No content')
        print(f"✅ Response: {content}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return False

def main():
    print("=" * 50)
    print("OLLAMA LLAMA 3.2 1B TEST")
    print("=" * 50)
    
    # Check connection
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get('models', [])]
            print(f"✅ Connected to Ollama")
            print(f"   Available models: {models}")
        else:
            print(f"❌ Ollama returned: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return
    
    # Run tests
    print("\n" + "-" * 50)
    test_generate()
    test_chat()
    
    print("\n" + "=" * 50)
    print("Tests complete!")

if __name__ == "__main__":
    main()