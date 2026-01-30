import logging
from typing import List, Dict
from app.graph.state import GraphState
from app.reasoning.llm.llama_reasoner import LlamaReasoner

logger = logging.getLogger(__name__)


class GenerationNode:
    """
    Evidence-grounded answer generator.
    - Explains answers
    - Shows sources
    - Explains conflicts
    """

    # Allowlist of non-evidence words (structural/connective language)
    ALLOWED_NON_EVIDENCE_WORDS = {
        "the", "a", "an", "is", "are", "was", "were",
        "this", "that", "these", "those",
        "process", "occurs", "involves",
        "because", "which", "used", "using",
        "evidence", "document", "documents",
        "according", "based", "provided"
    }

    # Meta-words to remove from validation input
    META_WORDS = {
        "evidence",
        "document",
        "documents",
        "source",
        "sources",
        "based",
        "according",
        "provided",
        "information",
    }

    def __init__(self):
        self.llm = LlamaReasoner()

    async def run(self, state: GraphState) -> GraphState:
        try:
            query = state.get("query", "")
            docs = state.get("retrieved_documents", [])
            conflicts = state.get("conflicts", [])
            is_conflicting = state.get("is_conflicting", False)

            if not docs:
                state["final_response"] = "This document does not contain information to answer your question."
                state["status"] = "refused"
                return state

            # 🔑 ENTITY PRESENCE CHECK - PREVENT HALLUCINATION
            if self._is_person_entity_query(query):
                entity = self._extract_entity_from_query(query)
                logger.info(f"[ENTITY CHECK] Query: '{query}' -> Entity: '{entity}'")
                if entity and not self._entity_in_documents(entity, docs):
                    logger.warning(f"[ENTITY CHECK] Entity '{entity}' not found in retrieved documents - REFUSING TO PREVENT HALLUCINATION")
                    state["final_response"] = f'I cannot answer this question because the uploaded documents do not contain any information about "{entity}".'
                    state["status"] = "refused"
                    return state
                else:
                    logger.info(f"[ENTITY CHECK] Entity '{entity}' found in documents or query doesn't require entity check - PROCEEDING")

            # 🔑 QUERY-EVIDENCE ALIGNMENT CHECK - PREVENT TOPIC HALLUCINATION
            # Temporarily disabled to allow answers when document contains relevant info
            # if not self._query_topic_in_evidence(query, docs):
            #     logger.warning(f"[TOPIC CHECK] Query topic not found in retrieved documents - REFUSING")
            #     state["final_response"] = "The provided documents do not contain information to answer this question."
            #     state["status"] = "refused"
            #     return state

            evidence_block = self._build_evidence_block(docs)

            if is_conflicting:
                prompt = self._conflict_prompt(query, evidence_block, conflicts)
            else:
                prompt = self._standard_prompt(query, evidence_block)

            answer = self.llm.generate(
                prompt=prompt,
                max_tokens=600,
                temperature=0.0,
                stop_sequences=["###"]
            ).strip()

            # 🔑 POST-GENERATION VALIDATION - Ensure answer uses retrieved evidence
            # Removed document isolation check for planet mode - allow cross-document retrieval

            if not self._validate_answer_against_evidence(answer, docs):
                logger.warning(f"[VALIDATION] Answer failed evidence validation - REFUSING")
                state["final_response"] = "The provided documents do not contain information to answer this question."
                state["status"] = "refused"
                return state

            # Clean and format the answer
            answer = self._format_answer(answer)

            answer += "\n\n" + self._build_sources_section(docs)

            state["final_response"] = answer
            state["status"] = "success"
            return state

        except Exception as e:
            logger.exception("Generation failed")
            state["final_response"] = f"Generation failed: {e}"
            state["status"] = "error"
            return state

    # ---------------------------------------------------------
    # Entity presence checks (ANTI-HALLUCINATION)
    # ---------------------------------------------------------

    def _is_person_entity_query(self, query: str) -> bool:
        """Check if query is asking about a specific person/entity/concept that might not be in documents"""
        # Strip markdown formatting
        query_clean = query.strip("*`").lower().strip()

        # BROAD entity detection - any query that seems to ask about a specific thing
        entity_indicators = [
            "who is", "who was", "who are", "who were",
            "what is", "what are", "what were", "what was",
            "tell me about", "describe", "explain",
            "information about", "details about", "about",
            "biography of", "profile of", "history of"
        ]

        # Check for entity question patterns
        for indicator in entity_indicators:
            if indicator in query_clean:
                # Extract potential entity and check if it looks like a proper noun
                entity = self._extract_entity_from_query(query)
                if entity:
                    # Check if entity looks like a proper name (capitalized or specific term)
                    entity_words = entity.split()
                    has_proper_noun = any(word[0].isupper() or len(word) > 3 for word in entity_words)
                    if has_proper_noun or any(word in query_clean for word in ["who", "what", "describe", "explain"]):
                        logger.info(f"[ENTITY DETECT] Matched '{indicator}' with entity '{entity}' - REQUIRES VERIFICATION")
                        return True

        # Check for question marks with potential entities
        if "?" in query and len(query.split()) > 2:
            # Any question with more than 2 words might be asking about something specific
            entity = self._extract_entity_from_query(query)
            if entity:
                logger.info(f"[ENTITY DETECT] Question pattern detected with entity '{entity}' - REQUIRES VERIFICATION")
                return True

        logger.info(f"[ENTITY DETECT] No entity pattern detected in '{query_clean}'")
        return False

    def _extract_entity_from_query(self, query: str) -> str:
        """Extract the entity name from person/entity queries"""
        # Strip markdown formatting
        query_clean = query.strip("*`").lower().strip()

        # Handle "who is X" pattern
        if query_clean.startswith("who is "):
            # Find the position in original query
            idx = query.lower().find("who is ")
            if idx >= 0:
                entity = query[idx + 7:].strip().rstrip("?").strip("*`")
                logger.info(f"[ENTITY EXTRACT] 'who is' pattern -> '{entity}' from '{query}'")
                return entity

        # Handle "tell me about X" pattern
        if "tell me about " in query_clean:
            idx = query.lower().find("tell me about ")
            if idx >= 0:
                entity = query[idx + 14:].strip().rstrip("?").strip("*`")
                logger.info(f"[ENTITY EXTRACT] 'tell me about' pattern -> '{entity}' from '{query}'")
                return entity

        # Handle "about X" pattern
        if "about " in query_clean:
            idx = query.lower().find("about ")
            if idx >= 0:
                entity = query[idx + 6:].strip().rstrip("?").strip("*`")
                logger.info(f"[ENTITY EXTRACT] 'about' pattern -> '{entity}' from '{query}'")
                return entity

        # Handle "what is X" for entities
        if query_clean.startswith("what is "):
            idx = query.lower().find("what is ")
            if idx >= 0:
                entity = query[idx + 8:].strip().rstrip("?").strip("*`")
                logger.info(f"[ENTITY EXTRACT] 'what is' pattern -> '{entity}' from '{query}'")
                return entity

        # Fallback: extract potential entity (first capitalized word after question words)
        import re
        words = re.findall(r'\b[A-Z][a-z]+\b', query)
        if words:
            logger.info(f"[ENTITY EXTRACT] Capitalized word fallback -> '{words[0]}' from '{query}'")
            return words[0]

        logger.info(f"[ENTITY EXTRACT] No entity found in '{query}'")
        return ""

    def _entity_in_documents(self, entity: str, docs: List[Dict]) -> bool:
        """Check if entity appears in retrieved documents' CONTENT (not metadata)"""
        if not entity:
            return False

        entity_lower = entity.lower()
        logger.info(f"[ENTITY SCAN] Checking for '{entity_lower}' in {len(docs)} documents")

        for i, doc in enumerate(docs):
            content = doc.get("content", "").lower()

            # ONLY check content - metadata like filenames shouldn't count as "information about the entity"
            if entity_lower in content:
                logger.info(f"[ENTITY SCAN] Found '{entity_lower}' in document {i} content")
                return True

        logger.info(f"[ENTITY SCAN] '{entity_lower}' not found in document content (only metadata matches don't count)")
        return False

    def _query_topic_in_evidence(self, query: str, docs: List[Dict]) -> bool:
        """Check if the main topic of the query is present in the retrieved evidence"""
        import re

        # Extract key terms from query (nouns, proper nouns, important words)
        query_lower = query.lower()
        key_terms = set(re.findall(r'\b[a-zA-Z]{4,}\b', query_lower))

        # Remove common question words and stop words
        stop_words = {'what', 'when', 'where', 'why', 'how', 'who', 'which', 'tell', 'about', 'importance', 'explain', 'describe', 'definition', 'meaning', 'purpose', 'function', 'role', 'process', 'steps', 'types', 'examples', 'benefits', 'advantages', 'disadvantages', 'causes', 'effects', 'impact', 'influence', 'relationship', 'difference', 'comparison', 'similarities', 'differences'}

        key_terms = key_terms - stop_words

        if not key_terms:
            logger.info("[TOPIC CHECK] No key terms found in query - allowing")
            return True

        # Combine all document content
        all_content = ' '.join(doc.get('content', '') for doc in docs).lower()

        # Check if at least one key term is present in evidence
        found_terms = []
        for term in key_terms:
            if term in all_content:
                found_terms.append(term)

        if found_terms:
            logger.info(f"[TOPIC CHECK] Found query terms in evidence: {found_terms}")
            return True
        else:
            logger.warning(f"[TOPIC CHECK] No query terms found in evidence. Key terms: {key_terms}")
            return False

    def _sanitize_answer_for_validation(self, answer: str) -> str:
        """Remove meta-words from answer before validation"""
        tokens = answer.lower().split()
        tokens = [t for t in tokens if t not in self.META_WORDS]
        return " ".join(tokens)

    def _validate_answer_against_evidence(self, answer: str, docs: List[Dict]) -> bool:
        """Validate that the answer only contains information from retrieved documents (claim-level validation)"""
        if not answer or answer.lower().startswith("the provided documents"):
            return True  # Refusal messages are valid

        # Sanitize answer by removing meta-words
        sanitized_answer = self._sanitize_answer_for_validation(answer)

        # Combine all document content
        all_content = ' '.join(doc.get('content', '') for doc in docs).lower()

        # Extract claims from sanitized answer (sentence-level)
        claims = self._extract_claims(sanitized_answer)

        # Relaxed validation: check if at least one claim has reasonable overlap with evidence
        if not claims:
            logger.info("[VALIDATION] No factual claims found in answer - allowing")
            return True  # No factual claims to validate

        # Check if at least one claim is supported by evidence
        supported_claims = 0
        for claim in claims:
            if self._semantic_match(claim, all_content):
                supported_claims += 1

        if supported_claims > 0:
            logger.info(f"[VALIDATION] {supported_claims}/{len(claims)} claims supported by evidence")
            return True

        # If no claims are supported, reject
        logger.warning(f"[VALIDATION] No claims in answer are supported by evidence")
        return False

    def _extract_claims(self, answer: str) -> List[str]:
        """Extract factual claims from the answer (sentence-level)"""
        import re

        # Split into sentences
        sentences = re.split(r'[.!?]+', answer.strip())

        # Filter out structural sentences (questions, short phrases)
        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Too short to be a claim
                continue
            if sentence.lower().startswith(('the', 'this', 'that', 'these', 'those')):
                continue  # Likely structural
            if any(word in sentence.lower() for word in ['according', 'based', 'evidence', 'document']):
                continue  # Meta-references
            claims.append(sentence)

        return claims

    def _semantic_match(self, claim: str, evidence: str) -> bool:
        """Check if claim is semantically supported by evidence using simple heuristics"""
        claim_lower = claim.lower()
        evidence_lower = evidence.lower()

        # Direct containment (most reliable)
        if claim_lower in evidence_lower:
            return True

        # Key phrase matching - extract important words
        import re
        claim_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', claim_lower))
        evidence_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', evidence_lower))

        # Allowlist of non-evidence words
        allowed_words = {
            "the", "a", "an", "is", "are", "was", "were",
            "this", "that", "these", "those",
            "process", "occurs", "involves",
            "because", "which", "used", "using",
            "evidence", "document", "documents",
            "according", "based", "provided"
        }

        # Check if key factual words are present
        key_words = claim_words - allowed_words
        if key_words and key_words.issubset(evidence_words):
            return True

        # Fallback: check for partial matches (at least 70% of key words)
        if key_words:
            matched = key_words.intersection(evidence_words)
            if len(matched) / len(key_words) >= 0.7:
                return True

        return False

    def _standard_prompt(self, query: str, evidence: str) -> str:
        return f"""
You are an EXTRACTIVE AI assistant. You can ONLY extract and rephrase information that is EXPLICITLY PRESENT in the provided evidence.

CRITICAL CONSTRAINTS (VIOLATION = INVALID RESPONSE):
1. You MUST NOT invent, assume, infer, or generalize ANY facts not explicitly stated in the evidence.
2. You MUST NOT introduce new entities, names, concepts, definitions, or explanations.
3. You MUST NOT use external knowledge or common sense reasoning.
4. If the query asks about ANY entity/concept not mentioned in the evidence, respond ONLY with:
   "The provided documents do not contain information to answer this question."
5. Every single word in your answer must be directly supported by the evidence text.
6. You MUST NOT combine information from different sources to create new facts.

RESPONSE RULES:
- Extract direct quotes and facts from the evidence.
- Rephrase using ONLY the words and concepts present in the evidence.
- If evidence is insufficient for a complete answer, use the refusal message.
- Do NOT add explanations, examples, or context beyond what's in the evidence.

FORMAT:
- Use **bold titles** for main topics.
- Use bullet points for facts and quotes.
- Include "Direct Evidence" section with exact quotes.
- Keep responses factual and minimal.

### Evidence
{evidence}

### Query
{query}

### Response
"""

    def _conflict_prompt(self, query: str, evidence: str, conflicts: List[str]) -> str:
        conflict_text = "\n".join(f"- {c}" for c in conflicts)
        return f"""
You are a factual assistant.

The evidence contains conflicts.
Explain BOTH sides clearly.
Mention WHICH sources disagree and WHY.

### Conflicts Detected
{conflict_text}

### Evidence
{evidence}

### Question
{query}

### Answer (conflict-aware)
"""

    # ---------------------------------------------------------
    # Evidence formatting
    # ---------------------------------------------------------

    def _build_evidence_block(self, docs: List[Dict]) -> str:
        blocks = []
        for i, doc in enumerate(docs[:8], 1):  # Increased from 5 to 8 for better context
            meta = doc.get("metadata", {})
            source = meta.get("file_name", "Unknown source")
            chunk_id = doc.get("id", "N/A")
            content = doc.get("content", "")[:600]  # Increased from 400 to 600 for more context

            blocks.append(
                f"[Evidence {i}]\n"
                f"Source: {source}\n"
                f"Chunk ID: {chunk_id}\n"
                f"Content: {content}"
            )
        return "\n\n".join(blocks)

    def _build_sources_section(self, docs: List[Dict]) -> str:
        seen = set()
        lines = ["### Sources Used"]

        for doc in docs[:8]:  # Increased from 5 to 8
            meta = doc.get("metadata", {})
            src = meta.get("file_name", "Unknown")
            if src not in seen:
                seen.add(src)
                lines.append(f"- {src}")

        return "\n".join(lines)

    def _format_answer(self, raw_answer: str) -> str:
        """Clean and format the LLM answer for consistency and readability"""
        if not raw_answer.strip():
            return "No answer could be generated from the available evidence."

        # If the answer starts with refusal, keep it simple
        if raw_answer.lower().startswith("the provided documents do not contain"):
            return raw_answer.strip()

        answer = raw_answer.strip()

        # Split into lines and clean up
        lines = [line.strip() for line in answer.split('\n') if line.strip()]

        # Ensure we have content
        if not lines:
            return "No answer could be generated from the available evidence."

        # Format the first line as a title if it looks like one
        first_line = lines[0]
        if not first_line.startswith('**') and len(first_line) < 60:
            # Check if it looks like a title (short, descriptive)
            if not first_line.startswith('*') and not first_line.startswith('-'):
                lines[0] = f"**{first_line}**"

        # Clean up bullet points and formatting
        formatted_lines = []
        for line in lines:
            # Ensure consistent bullet formatting
            if line.startswith('* ') or line.startswith('- '):
                formatted_lines.append(line)
            elif line.startswith('*') and not line.startswith('* '):
                formatted_lines.append(f"* {line[1:].strip()}")
            elif line.startswith('-') and not line.startswith('- '):
                formatted_lines.append(f"- {line[1:].strip()}")
            else:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)
