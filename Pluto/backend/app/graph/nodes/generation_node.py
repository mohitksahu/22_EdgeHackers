from app.reasoning.llm.llama_reasoner import LlamaReasoner
from app.graph.state import GraphState
import logging

logger = logging.getLogger(__name__)

class GenerationNode:
    """Node D: Plain Text Answer Generation (LLaMA outputs text ONLY)"""
    def __init__(self):
        self.llama_client = LlamaReasoner()

    async def run(self, state: GraphState) -> GraphState:
        """Generate plain text answer from evidence. Conflict-aware generation."""
        try:
            query = state.get('query', '')
            retrieved_docs = state.get('retrieved_documents', [])
            is_conflicting = state.get('is_conflicting', False)
            conflicts = state.get('conflicts', [])
            conversation_history = state.get('conversation_history', [])
            
            # Check if we should use conflict-aware prompt
            if is_conflicting and conflicts:
                prompt = self._build_conflict_aware_prompt(retrieved_docs, query, conflicts, conversation_history)
            else:
                prompt = self._build_plain_text_prompt(retrieved_docs, query, conversation_history)
            
            # Call LLM EXACTLY ONCE with strict parameters
            # Add stop tokens to prevent repetition
            answer_text = self.llama_client.generate(
                prompt, 
                max_tokens=400,  # Increased for conflict explanations
                stop_sequences=["\n\nEvidence", "\n\nUser Question", "Answer:", "\n\n\n"]
            )
            answer_text = answer_text.strip()
            
            # Remove escaped quotes and unwanted formatting
            answer_text = answer_text.strip('"\'\'\'\'"')
            
            # Remove any accidental repetitions
            answer_text = self._remove_repetitions(answer_text)
            
            # Add source citations using bracketed notation
            answer_text = self._add_citations(answer_text, retrieved_docs)
            
            logger.info(f"[GENERATION] LLaMA output (conflict-aware={is_conflicting}): {answer_text[:100]}...")
            
            # Store plain text answer in state
            state['final_response'] = answer_text
            state['status'] = 'success'
            
            return state
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            state['final_response'] = "An error occurred during response generation."
            state['status'] = 'error'
            return state

    def _build_plain_text_prompt(self, retrieved_docs: list, query: str, conversation_history: list = None) -> str:
        """
        Build simple plain text prompt for LLaMA.
        LLaMA outputs PLAIN TEXT answer - NO JSON, NO metadata, NO sources.
        Includes conversation history for follow-up questions.
        """
        # Build conversation context if history exists
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            conversation_context = "Previous Conversation:\n"
            for turn in conversation_history[-3:]:  # Last 3 turns only
                user_q = turn.get('user_query', '')
                system_resp = turn.get('system_response', '')[:200]  # First 200 chars
                conversation_context += f"User: {user_q}\nAssistant: {system_resp}\n\n"
            conversation_context += "---\n\n"
        
        # Build evidence context - combine ALL evidence into ONE string
        evidence_parts = []
        for idx, doc in enumerate(retrieved_docs[:5], 1):  # Top 5 docs
            content = doc.get('content', '')
            if content:
                evidence_parts.append(f"Evidence {idx}: {content[:300]}")
        
        evidence_context = "\n\n".join(evidence_parts) if evidence_parts else ""
        has_evidence = len(evidence_parts) > 0
        
        # STRICT PLAIN TEXT PROMPT - Enforce single answer, no JSON, no repetition
        prompt = f"""You are a retrieval-grounded assistant.
Answer ONLY using the provided evidence.
If evidence exists, you MUST answer.
Return ONE concise plain-text answer.
Do NOT repeat sentences.
Do NOT output JSON or lists.
Do NOT mention sources or files.

{conversation_context}Evidence:
{evidence_context if has_evidence else 'No evidence available.'}

User Question: {query}

Answer (plain text only, no repetition):""" 
        
        return prompt
    
    def _build_conflict_aware_prompt(self, retrieved_docs: list, query: str, conflicts: list, conversation_history: list = None) -> str:
        """
        Build conflict-aware prompt when contradictions are detected.
        Presents both sides and acknowledges uncertainty.
        Includes conversation history for context.
        """
        # Build conversation context if history exists
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            conversation_context = "Previous Conversation:\n"
            for turn in conversation_history[-3:]:  # Last 3 turns only
                user_q = turn.get('user_query', '')
                system_resp = turn.get('system_response', '')[:200]  # First 200 chars
                conversation_context += f"User: {user_q}\nAssistant: {system_resp}\n\n"
            conversation_context += "---\n\n"
        
        # Build evidence context - label conflicting sources
        evidence_parts = []
        for idx, doc in enumerate(retrieved_docs[:5], 1):
            content = doc.get('content', '')
            source_name = doc.get('metadata', {}).get('file_path', f'Source {idx}')
            if content:
                evidence_parts.append(f"Source {idx} ({source_name}): {content[:300]}")
        
        evidence_context = "\n\n".join(evidence_parts) if evidence_parts else ""
        
        # Format conflicts
        conflict_summary = "\n".join([f"- {c}" for c in conflicts])
        
        # CONFLICT-AWARE PROMPT
        prompt = f"""You are a retrieval-grounded assistant trained to acknowledge contradictions.

The evidence contains CONFLICTING information:
{conflict_summary}

{conversation_context}Evidence from multiple sources:
{evidence_context}

User Question: {query}

INSTRUCTIONS:
Since there are contradictions, you MUST present both perspectives.
Use this EXACT format:

"There is a conflict in the evidence. [Source A name] indicates [perspective A], whereas [Source B name] suggests [perspective B]. Based on the available evidence, [provide your reasoned assessment if possible, or state that more information is needed]."

Answer (acknowledge conflict, present both sides):"""
        
        return prompt
    
    def _remove_repetitions(self, text: str) -> str:
        """Remove repeated sentences from LLM output."""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        seen = set()
        unique_sentences = []
        for sentence in sentences:
            if sentence.lower() not in seen:
                seen.add(sentence.lower())
                unique_sentences.append(sentence)
        return '. '.join(unique_sentences) + ('.' if unique_sentences else '')
    
    def _add_citations(self, text: str, documents: list) -> str:
        """Add source citations to the answer using bracketed notation."""
        if not documents:
            return text
        
        # Get unique sources with page numbers
        citations = []
        seen_sources = set()
        
        for doc in documents[:5]:  # Top 5 sources
            metadata = doc.get('metadata', {})
            source_path = metadata.get('source_file') or metadata.get('file_path', 'Unknown')
            
            # Extract filename from full path (handle Windows and Unix paths)
            if isinstance(source_path, str):
                # Normalize path separators (handle both \ and /)
                source_path = source_path.replace('\\', '/').replace('\\', '/')
                # Extract just the filename
                if '/' in source_path:
                    filename = source_path.split('/')[-1]
                else:
                    filename = source_path
            else:
                filename = 'Unknown'
            
            page = metadata.get('page_number')
            
            # Create citation string
            if page:
                citation = f"{filename}, Page {page}"
            else:
                citation = filename
            
            if citation not in seen_sources:
                seen_sources.add(citation)
                citations.append(citation)
        
        # Append citations to answer
        if citations:
            citation_text = " [" + "; ".join(citations) + "]"
            return text + citation_text
        
        return text
