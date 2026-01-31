"""
Prometheus metrics middleware
"""
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
ACTIVE_SESSIONS = Gauge('active_sessions_total', 'Number of active sessions')
VECTOR_STORE_SIZE = Gauge('vector_store_documents_total', 'Total documents in vector store')
EMBEDDING_CACHE_HITS = Counter('embedding_cache_hits_total', 'Embedding cache hits')
EMBEDDING_CACHE_MISSES = Counter('embedding_cache_misses_total', 'Embedding cache misses')

async def metrics_middleware(request, call_next):
    """Record request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response