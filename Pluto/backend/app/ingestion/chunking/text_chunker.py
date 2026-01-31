# Micro-Chunking Shield using RecursiveCharacterTextSplitter
from typing import List, Dict
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter

def micro_chunk_text(text: str, chunk_size: int = 235, chunk_overlap: int = 30) -> List[Dict]:
	"""
	Splits text into micro-chunks of specified size to fit CLIP's 77-token (235-char) limit.
	Includes prev/next IDs for context stitching.

	FIX 5: If chunk_size > CLIP limit, RE-CHUNK instead of capping.
	
	Args:
		text: Input text to chunk
		chunk_size: Maximum characters per chunk (default 235 for CLIP's 77-token limit)
		chunk_overlap: Overlap between chunks for context preservation
		
	Returns:
		List of chunk dictionaries with content, IDs, and linking metadata
	"""
	# FIX 5: If chunk exceeds CLIP limit, re-chunk instead of capping
	CLIP_MAX_CHARS = 235
	if chunk_size > CLIP_MAX_CHARS:
		import logging
		logging.warning(f"chunk_size {chunk_size} exceeds CLIP limit, re-chunking with size={CLIP_MAX_CHARS}")
		# Re-chunk with proper size instead of just capping
		chunk_size = CLIP_MAX_CHARS
		# Increase overlap slightly to preserve context across re-chunked boundaries
		chunk_overlap = min(chunk_overlap, 50)
	
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
