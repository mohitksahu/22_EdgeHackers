"""
Reset Qdrant Vector Store - Clean Slate Utility

Use this script to clear all previous documents from the vector store.
This prevents semantic drift where the model finds "best matches" in irrelevant old data.

Usage:
    python scripts/reset_vectorstore.py
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.storage.vector_store import reset_vector_store
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Reset the vector store to start fresh"""
    logger.info("=" * 60)
    logger.info("QDRANT RESET UTILITY")
    logger.info("=" * 60)

    logger.info(f"Target Qdrant instance: {settings.qdrant_host}:{settings.qdrant_port}")
    logger.info(f"Collection: {settings.collection_name}")

    # Confirm before deletion
    response = input("\n⚠️  This will DELETE all existing documents. Continue? (yes/no): ")

    if response.lower() != 'yes':
        logger.info("Reset cancelled by user.")
        return

    # Perform reset
    success = reset_vector_store()

    if success:
        logger.info("\n✅ Vector store reset successfully!")
        logger.info("You can now ingest new documents with a clean slate.")
    else:
        logger.error("\n❌ Reset failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
