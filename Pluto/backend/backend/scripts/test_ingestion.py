import os
from pathlib import Path
from app.ingestion.orchestrator import ingest_file
from app.storage.chromadb.collections import get_pluto_main_collection
from app.ingestion.validators.file_validator import FileValidator

TEST_FILES = [
    os.path.join(os.path.dirname(__file__), '../test_assets/ruby_substrate.txt'),
    os.path.join(os.path.dirname(__file__), '../test_assets/red_circuit_board.jpg'),
]

def test_ingestion():
    print("Testing ingestion pipeline...")
    validator = FileValidator()
    for file_path in TEST_FILES:
        print(f"\nValidating: {file_path}")
        assert validator.validate(file_path), f"Validation failed: {validator.errors}"
        print("Validation passed.")
        doc_ids = ingest_file(file_path)
        print(f"Ingested doc IDs: {doc_ids}")
        assert doc_ids, "No document IDs returned!"
        # Check ChromaDB
        collection = get_pluto_main_collection()
        results = collection.get(ids=doc_ids)
        for i, doc_id in enumerate(doc_ids):
            print(f"Checking doc_id: {doc_id}")
            # Embedding check
            embedding = results['embeddings'][i]
            assert embedding is not None, f"No embedding for {doc_id}"
            assert len(embedding) == 512, f"Embedding for {doc_id} is not 512-dim: {len(embedding)}"
            # Metadata check
            metadata = results['metadatas'][i]
            assert 'file_path' in metadata, f"Missing file_path in metadata for {doc_id}"
            assert 'modality' in metadata, f"Missing modality in metadata for {doc_id}"
            print(f"Metadata: {metadata}")
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_ingestion()
