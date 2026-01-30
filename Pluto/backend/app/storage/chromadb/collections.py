import chromadb
from chromadb.config import Settings
import os
from app.config import settings

# Use the chromadb directory from config (points to f:/Pluto/data/vectorstore/chromadb)
CHROMA_PERSIST_DIR = str(settings.chromadb_dir)

def get_chroma_client():
	return chromadb.PersistentClient(
		path=CHROMA_PERSIST_DIR, 
		settings=Settings(
			allow_reset=True,
			anonymized_telemetry=False
		)
	)

def get_pluto_main_collection():
	"""DEPRECATED: Use ChromaDBClient instead. This function uses the correct collection_name from settings."""
	client = get_chroma_client()
	# Use collection_name from settings instead of hardcoded 'pluto_main'
	collection = client.get_or_create_collection(
		name=settings.collection_name,  # FIXED: was 'pluto_main'
		metadata={"hnsw:space": "cosine"}
	)
	return collection
