import logging
import uuid
from typing import List, Dict, Any, Optional
from app.storage.chromadb.client import ChromaDBClient
from app.embeddings.manager import EmbeddingsManager

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.client = ChromaDBClient()
        self.embedder = EmbeddingsManager()

    def add_documents(self, chunks: List[Dict[str, Any]]):
        embeddings, metadatas, ids, documents = [], [], [], []

        for chunk in chunks:
            content = chunk["content"]
            embeddings.append(chunk["embedding"])
            documents.append(content)
            ids.append(chunk.get("id", str(uuid.uuid4())))
            metadatas.append(chunk["metadata"])

        self.client.add_documents(
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
            documents=documents,
        )

        return {"status": "success", "count": len(ids)}

    def query(self, query_text: str, scope_id: str, n_results: int = 10):
        query_embedding = self.embedder.embed_text(query_text)

        return self.client.query_documents(
            query_embedding=query_embedding,
            n_results=n_results,
            where={"scope_id": scope_id},
        )

    def delete_by_scope_and_source(self, scope_id: str, source_file: str) -> int:
        return self.client.delete_where({
            "scope_id": scope_id,
            "source_file": source_file
        })

    def clear_collection(self) -> int:
        """Clear all documents from the vector store"""
        return self.client.clear_collection()

    def reset(self) -> int:
        """Alias for clear_collection for API compatibility"""
        return self.clear_collection()
