# Micro-Chunking Shield using RecursiveCharacterTextSplitter
from typing import List, Dict
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter

def micro_chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict]:
	"""
	Splits text into micro-chunks of specified size for better context preservation.
	Includes prev/next IDs for context stitching.

	Args:
		text: Input text to chunk
		chunk_size: Maximum characters per chunk (default 1000 for better context)
		chunk_overlap: Overlap between chunks for context preservation (default 200)
		
	Returns:
		List of chunk dictionaries with content, IDs, and linking metadata
	"""
	# CLIP can handle larger chunks, but warn if extremely large
	CLIP_MAX_CHARS = 2000  # Increased limit for better context
	if chunk_size > CLIP_MAX_CHARS:
		import logging
		logging.warning(f"chunk_size {chunk_size} exceeds recommended CLIP limit, using {CLIP_MAX_CHARS}")
		chunk_size = CLIP_MAX_CHARS
		chunk_overlap = min(chunk_overlap, 400)  # Allow larger overlap for very large chunks
	
	splitter = RecursiveCharacterTextSplitter(
		chunk_size=chunk_size,
		chunk_overlap=chunk_overlap,
		length_function=len,
		separators=["\n\n", "\n", ". ", " ", ""]
	)
	raw_chunks = splitter.split_text(text)
	processed_chunks = []
	chunk_ids = [str(uuid.uuid4()) for _ in range(len(raw_chunks))]
	parent_id = str(uuid.uuid4())  # Parent ID for grouped sub-chunks
	
	for i, chunk_content in enumerate(raw_chunks):
		processed_chunks.append({
			"id": chunk_ids[i],
			"chunk": chunk_content,
			"prev_chunk_id": chunk_ids[i-1] if i > 0 else None,
			"next_chunk_id": chunk_ids[i+1] if i < len(chunk_ids) - 1 else None,
			"parent_chunk_id": parent_id  # Link sub-chunks to parent
		})
	return processed_chunks
