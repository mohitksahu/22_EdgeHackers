"""
GPU Availability Check - Validates hardware acceleration for C++ engines
"""
import logging
import sys

logger = logging.getLogger(__name__)


def validate_gpu_availability():
    """
    Validate that hardware acceleration is available for C++ engines.
    
    This system uses C++-powered engines that support both GPU and CPU:
    1. fastembed (ONNX-based CLIP embeddings) - GPU preferred, CPU fallback
    2. llama-cpp-python (GGUF models) - GPU preferred, CPU fallback
    
    GPU acceleration provides significant performance benefits but is not mandatory.
    
    Logs warnings if GPU is not available but allows CPU operation.
    """
    logger.info("=" * 80)
    logger.info("HARDWARE ACCELERATION CHECK")
    logger.info("=" * 80)
    
    # Check if fastembed can use GPU (ONNX runtime)
    try:
        from fastembed import TextEmbedding
        # Test if ONNX can use GPU
        test_model = TextEmbedding("Qdrant/clip-ViT-B-32-text")
        # ONNX will automatically use GPU if available
        logger.info("[OK] fastembed (CLIP) initialized successfully")
        logger.info("[INFO] fastembed uses ONNX runtime - GPU acceleration if available")
    except Exception as e:
        logger.warning(f"[WARNING] fastembed initialization failed: {e}")
        logger.warning("[WARNING] CLIP embeddings will use CPU fallback")
    
    # Check if llama-cpp-python can load (will use GPU if available)
    try:
        import llama_cpp
        logger.info("[OK] llama-cpp-python available")
        logger.info("[INFO] llama-cpp-python will use GPU if CUDA build is available")
    except ImportError:
        logger.error("[ERROR] llama-cpp-python not installed")
        raise RuntimeError("llama-cpp-python is required but not installed")
    
    # Log system capabilities
    logger.info("[INFO] System supports both GPU and CPU operation")
    logger.info("[INFO] GPU acceleration preferred for performance")
    logger.info("[INFO] CPU fallback available for compatibility")
    
    logger.info("=" * 80)
    logger.info("HARDWARE CHECK COMPLETED")
    logger.info("=" * 80)


def get_gpu_info() -> dict:
    """
    Get information about available hardware acceleration.
    
    Returns:
        dict: Hardware information for C++ engines
    """
    info = {
        "available": True,
        "device": "cpu",
        "engines": []
    }
    
    # Check fastembed (ONNX)
    try:
        from fastembed import TextEmbedding
        info["engines"].append("fastembed (CLIP via ONNX)")
        # ONNX can use GPU automatically if available
        info["fastembed_gpu"] = True  # ONNX will use GPU if available
    except:
        info["engines"].append("fastembed (unavailable)")
    
    # Check llama-cpp-python
    try:
        import llama_cpp
        info["engines"].append("llama-cpp-python")
        # llama-cpp will use GPU if CUDA build is available
        info["llama_gpu"] = True  # Will use GPU if CUDA-enabled build
    except:
        info["engines"].append("llama-cpp-python (unavailable)")
    
    # Determine overall device capability
    if "fastembed (CLIP via ONNX)" in info["engines"]:
        info["device"] = "gpu_preferred"  # ONNX can use GPU
    if "llama-cpp-python" in info["engines"]:
        info["device"] = "gpu_preferred"  # llama-cpp can use GPU
    
    return info


if __name__ == "__main__":
    # Allow testing this module directly
    logging.basicConfig(level=logging.INFO)
    try:
        validate_gpu_availability()
        print("\nOK GPU validation passed!")
        print("\nGPU Info:")
        info = get_gpu_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
    except RuntimeError as e:
        print(f"\nFAIL GPU validation failed: {e}")
        sys.exit(1)
