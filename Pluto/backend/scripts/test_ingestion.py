import os
from pathlib import Path
from app.ingestion.orchestrator import ingest_file
from app.storage.qdrant.collections import get_qdrant_client
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
        # Check Qdrant
        client = get_qdrant_client()
        # For now, just check that points were created
        # TODO: Implement proper point retrieval for testing
        collection_info = client.get_collection()
        print(f"Collection points count: {collection_info.points_count}")
        assert collection_info.points_count > 0, "No points found in collection"
        print("Points successfully stored in Qdrant")
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_ingestion()
