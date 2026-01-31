#!/usr/bin/env python3
"""
Check Ollama GPU configuration and fix issues
"""
import subprocess
import requests
import json
import sys

OLLAMA_HOST = "http://localhost:11434"
MODEL = "llama3.2:1b"


def check_nvidia_gpu():
    """Check if NVIDIA GPU is available"""
    print("=" * 60)
    print("CHECKING NVIDIA GPU")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", 
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("[OK] NVIDIA GPU detected:")
            for line in result.stdout.strip().split('\n'):
                parts = line.split(',')
                if len(parts) >= 4:
                    print(f"  GPU: {parts[0].strip()}")
                    print(f"  VRAM Total: {parts[1].strip()} MB")
                    print(f"  VRAM Used: {parts[2].strip()} MB")
                    print(f"  Utilization: {parts[3].strip()}%")
            return True
        else:
            print("[FAIL] nvidia-smi failed")
            return False
    except FileNotFoundError:
        print("[FAIL] nvidia-smi not found. NVIDIA drivers may not be installed.")
        return False


def check_ollama_version():
    """Check Ollama version"""
    print("\n" + "=" * 60)
    print("CHECKING OLLAMA VERSION")
    print("=" * 60)
    
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        print(f"[OK] Ollama version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("[FAIL] Ollama not found")
        return False


def check_model_details():
    """Check model details and GPU layers"""
    print("\n" + "=" * 60)
    print("CHECKING MODEL GPU CONFIGURATION")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/show",
            json={"name": MODEL},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Model: {MODEL}")
            
            # Check model details
            details = data.get('details', {})
            print(f"  Parameter Size: {details.get('parameter_size', 'unknown')}")
            print(f"  Quantization: {details.get('quantization_level', 'unknown')}")
            print(f"  Family: {details.get('family', 'unknown')}")
            
            # Check modelfile for GPU settings
            modelfile = data.get('modelfile', '')
            if 'num_gpu' in modelfile.lower():
                print(f"  [INFO] num_gpu found in modelfile")
            
            return True
        else:
            print(f"[FAIL] Could not get model info: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_inference_with_gpu():
    """Test inference and check if GPU is used"""
    print("\n" + "=" * 60)
    print("TESTING INFERENCE WITH GPU MONITORING")
    print("=" * 60)
    
    # Start nvidia-smi monitoring in background
    print("Running inference...")
    
    try:
        # Run inference with explicit GPU settings
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL,
                "prompt": "Count from 1 to 5:",
                "options": {
                    "num_gpu": 99,  # Use all layers on GPU
                    "num_thread": 4,
                    "num_predict": 50
                },
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Response: {data.get('response', '')[:100]}")
            
            # Check eval metrics
            eval_count = data.get('eval_count', 0)
            eval_duration = data.get('eval_duration', 1)
            tokens_per_sec = eval_count / (eval_duration / 1e9) if eval_duration > 0 else 0
            
            print(f"\nPerformance Metrics:")
            print(f"  Tokens generated: {eval_count}")
            print(f"  Tokens/second: {tokens_per_sec:.2f}")
            
            # GPU inference is typically 20+ tokens/sec for 1B model
            if tokens_per_sec > 15:
                print(f"  [OK] Performance suggests GPU is being used")
            else:
                print(f"  [WARN] Performance is low - may be using CPU")
            
            return True
        else:
            print(f"[FAIL] Inference failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def check_ollama_ps():
    """Check running models"""
    print("\n" + "=" * 60)
    print("CHECKING RUNNING MODELS")
    print("=" * 60)
    
    try:
        result = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
        print(result.stdout)
        
        # The output shows GPU usage
        if "GPU" in result.stdout or "100%" in result.stdout:
            print("[OK] Model appears to be using GPU")
        elif "0%" in result.stdout:
            print("[WARN] Model may not be using GPU")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def fix_ollama_gpu():
    """Attempt to fix GPU issues"""
    print("\n" + "=" * 60)
    print("ATTEMPTING TO FIX GPU USAGE")
    print("=" * 60)
    
    print("""
To ensure Ollama uses your GPU:

1. Make sure CUDA is installed and nvidia-smi works
   
2. Restart Ollama service:
   - Close any running Ollama processes
   - Open a new terminal and run: ollama serve
   
3. Set environment variables (PowerShell):
   $env:OLLAMA_NUM_GPU=99
   ollama serve
   
4. Or set permanently:
   [System.Environment]::SetEnvironmentVariable('OLLAMA_NUM_GPU', '99', 'User')
   
5. Unload and reload the model:
   ollama stop llama3.2:1b
   ollama run llama3.2:1b

6. Check GPU memory with nvidia-smi while model is loaded
   - You should see ~1.5GB VRAM used by Ollama
""")


def main():
    print("=" * 60)
    print("OLLAMA GPU DIAGNOSTIC TOOL")
    print("=" * 60)
    
    has_gpu = check_nvidia_gpu()
    check_ollama_version()
    check_model_details()
    
    if has_gpu:
        test_inference_with_gpu()
        check_ollama_ps()
    
    fix_ollama_gpu()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()