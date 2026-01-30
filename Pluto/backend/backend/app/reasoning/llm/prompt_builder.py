"""
Prompt Builder for evidence-grounded generation
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def build_multimodal_prompt(retrieved_documents: List[Dict[str, Any]], 
                            query: Optional[str] = None) -> str:
    """
    Build a prompt for evidence-grounded generation with strict refusal enforcement
    
    Args:
        retrieved_documents: List of retrieved document dictionaries
        query: Optional query to include
        
    Returns:
        Formatted prompt string with evidence or explicit refusal instruction
    """
    # System prompt enforcing evidence-only responses
    system_prompt = """🔒 SYSTEM PROMPT — EVIDENCE-GATED RAG ENFORCEMENT
You are an Evidence-Grounded Reasoning Agent in a Multimodal RAG system.

CRITICAL RULES (MUST FOLLOW):
1. You are ONLY allowed to answer using the provided evidence.
2. You MUST NOT use your general or prior knowledge.
3. If the provided evidence is empty, insufficient, or irrelevant:
   - You MUST refuse to answer.
   - You MUST NOT attempt to explain the topic.
4. Refusal is REQUIRED when:
   - No documents are provided
   - Evidence does not directly support the query
   - Confidence cannot be established from evidence

ANSWER SUFFICIENCY RULES (MANDATORY):
5. Single-word, label-only, or entity-only responses are NOT valid answers.
6. For "who is / what is / explain" queries, you MUST provide a complete explanatory sentence.
7. If evidence only confirms existence (e.g., name mentioned once) without details:
   - You MUST explicitly state that limitation in your answer.
   - Example: "The evidence mentions [entity] but does not provide enough information to fully answer the question."
8. NEVER output just an entity name, label, or identifier as the answer.
9. Answers must be substantive, containing at least 8 words in a complete sentence.

REFUSAL FORMAT (MANDATORY):
If you refuse, respond ONLY with valid JSON in this exact structure:

{
  "refusal": true,
  "reason": "Insufficient or missing supporting evidence in the knowledge base.",
  "answer": null,
  "confidence": 0.0,
  "cited_sources": []
}

ANSWER FORMAT (ONLY IF EVIDENCE EXISTS):
If and only if evidence is sufficient, respond in valid JSON:

{
  "refusal": false,
  "answer": "<complete explanatory sentence strictly derived from evidence>",
  "confidence": <float between 0 and 1>,
  "cited_sources": [
    {
      "source_id": "<source identifier>",
      "modality": "<text | image | audio>"
    }
  ]
}

IMPORTANT:
- You must NEVER answer from memory.
- You must NEVER hallucinate.
- You must NEVER partially answer.
- You must NEVER give single-word or label-only responses.
- Silence or incomplete JSON is NOT allowed.
- Every answer must be a complete, informative sentence.
"""

    # Check if evidence exists
    if not retrieved_documents or len(retrieved_documents) == 0:
        return f"""{system_prompt}

Evidence:
[No evidence available]

Question: {query if query else 'N/A'}

You MUST respond with the refusal JSON format since no evidence is provided."""

    # Build context from retrieved documents
    context_parts = []
    source_map = {}
    
    for i, doc in enumerate(retrieved_documents[:10], 1):  # Limit to top 10
        content = doc.get('content', doc.get('text', ''))
        metadata = doc.get('metadata', {})
        modality = metadata.get('modality', 'unknown')
        source = metadata.get('source_file', 'unknown')
        
        source_id = f"evidence_{i}"
        source_map[source_id] = {
            "source": source,
            "modality": modality
        }
        
        # Format each piece of evidence
        context_parts.append(
            f"[{source_id}] (Source: {source}, Type: {modality})\n{content}\n"
        )

    context = "\n".join(context_parts)

    # Build the full prompt with evidence
    if query:
        prompt = f"""{system_prompt}

Evidence:
{context}

Question: {query}

IMPORTANT INSTRUCTIONS:
1. Respond with ONLY ONE valid JSON object - nothing else.
2. Do NOT include the template examples in your response.
3. Do NOT add conversational text like "Please let me know" or "I have a follow-up question".
4. Do NOT output multiple JSON objects.
5. Your ENTIRE response must be a single valid JSON object.

Respond NOW with your JSON (ANSWER format if evidence sufficient, REFUSAL format if not):"""
    else:
        prompt = f"""{system_prompt}

Evidence:
{context}

Provide a summary in valid JSON format based on the evidence above."""

    return prompt


def build_evaluation_prompt(query: str, evidence: List[str]) -> str:
    """
    Build a prompt for evidence evaluation
    
    Args:
        query: User query
        evidence: List of evidence strings
        
    Returns:
        Evaluation prompt
    """
    evidence_text = "\n\n".join([f"Evidence {i+1}: {e}" for i, e in enumerate(evidence)])

    prompt = f"""Evaluate whether the provided evidence is sufficient to answer this question:

Question: {query}

{evidence_text}

Evaluation:
1. Sufficiency: (Sufficient/Partial/Insufficient)
2. Confidence Level: (High/Medium/Low)
3. Missing Information: (if any)
4. Recommendation: (Answer/Request More Info/Refuse)

Provide your evaluation:"""

    return prompt


def build_conflict_detection_prompt(evidence_pieces: List[str]) -> str:
    """
    Build a prompt for detecting conflicts in evidence
    
    Args:
        evidence_pieces: List of evidence strings
        
    Returns:
        Conflict detection prompt
    """
    evidence_text = "\n\n".join([f"Statement {i+1}: {e}" for i, e in enumerate(evidence_pieces)])

    prompt = f"""Analyze these statements for contradictions or conflicts:

{evidence_text}

Analysis:
1. Are there any contradictions? (Yes/No)
2. If yes, describe the conflicts:
3. Which statements are most reliable?

Provide your analysis:"""

    return prompt
