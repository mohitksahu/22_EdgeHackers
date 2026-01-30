"""
ChromaDB client (STRICT SCOPE ISOLATION)
"""
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from app.config import settings

logger = logging.getLogger(__name__)


class ChromaDBClient:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(settings.chromadb_dir),
            settings=Settings(anonymized_telemetry=False)
        )

    def get_collection(self):
        return self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, embeddings, metadatas, ids, documents):
        self.get_collection().add(
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
            documents=documents,
        )

    def query_documents(self, query_embedding, n_results=10, where=None):
        logger.info(f"[ChromaDB] Querying with where={where}, n_results={n_results}")
        result = self.get_collection().query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
        logger.info(f"[ChromaDB] Query returned {len(result.get('documents', [[]])[0])} documents")
        return result

    def query(self, *args, **kwargs):
        """Alias for query_documents for compatibility"""
        return self.query_documents(*args, **kwargs)

    def get_documents_summary(self, scope_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get summary per document: topics, concepts, filename"""
        where = {"scope_id": scope_id} if scope_id else None
        results = self.get_collection().get(where=where)

        doc_summaries = {}

        for meta in results.get("metadatas", []):
            if not meta:
                continue
            filename = meta.get("source_file", "unknown")
            if filename not in doc_summaries:
                doc_summaries[filename] = {
                    "topics": set(),
                    "concepts": set(),
                    "filename": filename
                }
            if meta.get("document_topic"):
                doc_summaries[filename]["topics"].add(meta["document_topic"].lower())
            if meta.get("document_concepts"):
                for c in meta["document_concepts"].split(","):
                    doc_summaries[filename]["concepts"].add(c.strip().lower())

        # Convert sets to lists
        for doc in doc_summaries.values():
            doc["topics"] = list(doc["topics"])
            doc["concepts"] = list(doc["concepts"])

        return doc_summaries

    def delete_where(self, where: Dict[str, Any]) -> int:
        """Delete documents matching the where clause"""
        try:
            collection = self.get_collection()
            results = collection.get(where=where)
            ids_to_delete = results.get("ids", [])
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                logger.info(f"[ChromaDB] Deleted {len(ids_to_delete)} documents matching {where}")
            return len(ids_to_delete)
        except Exception as e:
            logger.error(f"[ChromaDB] Delete failed: {e}")
            return 0

    def clear_collection(self) -> int:
        """Clear all documents from the collection"""
        try:
            collection = self.get_collection()
            results = collection.get()
            ids_to_delete = results.get("ids", [])
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                logger.info(f"[ChromaDB] Cleared {len(ids_to_delete)} documents from collection")
            return len(ids_to_delete)
        except Exception as e:
            logger.error(f"[ChromaDB] Clear failed: {e}")
            return 0
