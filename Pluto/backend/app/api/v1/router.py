"""
API Router for version 1 endpoints
"""
from fastapi import APIRouter

from app.api.v1.endpoints import ingest, query, vector, session

# Create the main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    ingest.router,
    prefix="/ingest",
    tags=["ingestion"]
)

api_router.include_router(
    query.router,
    prefix="/query",
    tags=["query"]
)

api_router.include_router(
    vector.router,
    prefix="/vector",
    tags=["vector"]
)

api_router.include_router(
    session.router,
    prefix="/session",
    tags=["session"]
)