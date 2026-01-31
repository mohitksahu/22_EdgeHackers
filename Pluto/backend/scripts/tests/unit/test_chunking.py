import pytest
from app.ingestion.chunking.text_chunker import micro_chunk_text

def test_micro_chunking_and_token_safety():
    # 1,000-character string
    text = "A" * 1000
    chunks = micro_chunk_text(text)
    assert all(len(chunk['chunk']) <= 235 for chunk in chunks), "Chunk exceeds 235 characters!"
    for i, chunk in enumerate(chunks):
        # prev_chunk_id and next_chunk_id must be present (None for first/last)
        assert 'prev_chunk_id' in chunk and 'next_chunk_id' in chunk
        if i == 0:
            assert chunk['prev_chunk_id'] is None
        if i == len(chunks) - 1:
            assert chunk['next_chunk_id'] is None
        if 0 < i < len(chunks) - 1:
            assert chunk['prev_chunk_id'] is not None and chunk['next_chunk_id'] is not None
    print(f"Total chunks: {len(chunks)}. All chunk sizes and context IDs are valid.")
