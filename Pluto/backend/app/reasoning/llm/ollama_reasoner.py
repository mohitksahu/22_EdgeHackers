"""
Ollama Reasoner - LLM interface with grounding and conflict handling
Uses ONLY retrieved context to prevent hallucination
"""
import requests
from typing import Optional, Dict, Any, List

from app.config import settings
from app.core.logging_config import get_safe_logger

logger = get_safe_logger(__name__)


# System prompt for grounded, conflict-aware responses
SYSTEM_PROMPT = """You are PLUTO, an intelligent assistant that answers questions based ONLY on the provided context from uploaded documents.

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. ONLY use information from the provided context to answer questions
2. If the context doesn't contain relevant information, say: "I don't have information about that in the uploaded documents."
3. NEVER make up, invent, or hallucinate information not present in the context
4. ALWAYS cite your sources using [Source: filename, page X] format when available
5. If you find CONFLICTING information from different sources, present BOTH perspectives clearly:
   - "According to [Source A]: ..."
   - "However, [Source B] states: ..."
   - Then provide a balanced summary
6. Be concise but comprehensive in your answers
7. For images described in context, reference them as "The image from [source] shows..."
8. For audio transcriptions, mention "The audio recording states..."

RESPONSE FORMAT:
- Start with a direct answer to the question
- Support with evidence from the context
- Cite sources with filenames and page numbers
- If conflicts exist, explain both viewpoints fairly
- End with a brief summary for complex answers

Remember: You can ONLY use information from the provided context. If you don't know, say so."""


class OllamaReasoner:
    """
    Ollama-based LLM reasoner with context grounding
    Prevents hallucination by strictly using retrieved context
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OllamaReasoner, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if OllamaReasoner._initialized:
            return
        
        self.model = settings.ollama_model
        self.host = settings.ollama_host
        self.timeout = 120
        
        logger.info(f"Ollama Reasoner initialized with model: {self.model}")
        logger.info(f"Ollama host: {self.host}")
        
        self._verify_connection()
        
        OllamaReasoner._initialized = True
    
    def _verify_connection(self):
        """Verify Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                if self.model in models or any(self.model.split(':')[0] in m for m in models):
                    logger.info(f"[OK] Ollama ready with {self.model}")
                    self._warmup()
                else:
                    logger.warning(f"[WARN] Model {self.model} not found. Available: {models}")
        except Exception as e:
            logger.error(f"[FAIL] Ollama connection failed: {e}")
    
    def _warmup(self):
        """Warm up the model for faster first response"""
        logger.info("Warming up Ollama model...")
        try:
            self.generate("Hello", max_tokens=5)
            logger.info("Ollama model warmed up successfully")
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.3,
        system_prompt: str = None,
    ) -> str:
        """
        Generate response from Ollama
        
        Args:
            prompt: The user prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more focused/deterministic)
            system_prompt: Override system prompt
            
        Returns:
            Generated text response
        """
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt or SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Generate failed: {e}")
            return ""
    
    def generate_with_context(
        self,
        query: str,
        context: str,
        sources: List[Dict],
        has_conflicts: bool = False,
        chat_history: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Generate grounded response using retrieved context
        
        Args:
            query: User's question
            context: Retrieved context from documents (with source info)
            sources: Source attribution info
            has_conflicts: Whether conflicting info was found
            chat_history: Previous conversation turns
            
        Returns:
            Dict with response and metadata
        """
        # Build prompt with context
        prompt_parts = []
        
        # Add context from retrieved documents
        if context:
            prompt_parts.append("CONTEXT FROM UPLOADED DOCUMENTS:")
            prompt_parts.append("=" * 50)
            prompt_parts.append(context)
            prompt_parts.append("=" * 50)
        else:
            prompt_parts.append("NOTE: No relevant context found in uploaded documents.")
        
        # Add conflict warning if needed
        if has_conflicts:
            prompt_parts.append(
                "\n⚠️ IMPORTANT: The context contains information from MULTIPLE SOURCES "
                "that may have different perspectives. You MUST present ALL viewpoints fairly."
            )
        
        # Add chat history for context continuity
        if chat_history:
            prompt_parts.append("\nPREVIOUS CONVERSATION:")
            for turn in chat_history[-3:]:  # Last 3 turns
                prompt_parts.append(f"User: {turn.get('query', '')}")
                prompt_parts.append(f"Assistant: {turn.get('response', '')[:300]}...")
        
        # Add the question
        prompt_parts.append(f"\nUSER QUESTION: {query}")
        prompt_parts.append("\nProvide a helpful, accurate answer based ONLY on the context above. Cite your sources.")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        # Generate response
        response_text = self.generate(
            prompt=full_prompt,
            max_tokens=800,
            temperature=0.3
        )
        
        # Verify grounding
        is_grounded = self._verify_grounding(response_text, context)
        
        return {
            "response": response_text,
            "is_grounded": is_grounded,
            "sources_used": sources,
            "has_conflicts": has_conflicts,
            "context_length": len(context) if context else 0
        }
    
    def _verify_grounding(self, response: str, context: str) -> bool:
        """Verify response is grounded in context (not hallucinated)"""
        if not context:
            return True
        
        response_lower = response.lower()
        
        # Check for hallucination indicators
        hallucination_phrases = [
            "i think",
            "i believe", 
            "in my opinion",
            "generally speaking",
            "it's commonly known",
            "as everyone knows",
            "i would assume",
            "typically",
        ]
        
        for phrase in hallucination_phrases:
            if phrase in response_lower:
                logger.warning(f"[WARN] Potential hallucination detected: '{phrase}'")
                return False
        
        return True