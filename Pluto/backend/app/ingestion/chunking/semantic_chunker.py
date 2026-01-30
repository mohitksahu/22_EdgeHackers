# Semantic Chunker: Splits text into semantically coherent chunks using embeddings
from typing import List, Dict
import numpy as np
import re

def dummy_embed(text: str) -> np.ndarray:
	# Placeholder: Replace with your real embedding model (e.g., SentenceTransformer, OpenAI, etc.)
	# Returns a random vector for demonstration
	np.random.seed(abs(hash(text)) % (2**32))
	return np.random.rand(384)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
	return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

def semantic_chunk_text(text: str, similarity_threshold: float = 0.80) -> List[Dict]:
	"""
	Splits text into semantically coherent chunks by detecting topic shifts.
	Each chunk is a group of sentences with high semantic similarity.
	"""
	# Split text into sentences (simple regex, replace with better NLP if needed)
	sentences = re.split(r'(?<=[.!?])\s+', text.strip())
	if not sentences:
		return []
	chunks = []
	current_chunk = [sentences[0]]
	current_embedding = dummy_embed(sentences[0])
	for sent in sentences[1:]:
		sent_emb = dummy_embed(sent)
		sim = cosine_similarity(current_embedding, sent_emb)
		if sim < similarity_threshold:
			# Topic shift detected, start new chunk
			chunks.append(' '.join(current_chunk))
			current_chunk = [sent]
			current_embedding = sent_emb
		else:
			current_chunk.append(sent)
			# Update embedding as mean of chunk
			current_embedding = (current_embedding + sent_emb) / 2
	if current_chunk:
		chunks.append(' '.join(current_chunk))
	# Return as list of dicts for compatibility
	return [{
		'chunk': chunk,
		'start_sentence': i,
		'end_sentence': i + chunk.count('.') + chunk.count('!') + chunk.count('?')
	} for i, chunk in enumerate(chunks)]
