import logging
import re
from openai import OpenAI
from ..config import settings

logger = logging.getLogger(__name__)

def execute_live_rewrite(query: str) -> str:
    """
    Calls the LLM to rewrite a conversational query into an optimized semantic search query.
    """
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE
    )
    system_prompt = (
        "You are an expert search engine query optimizer. "
        "Your task is to rewrite the user's conversational search query into a concise list of "
        "search terms, keywords, and synonyms optimized for high-dimensional semantic vector search. "
        "Do NOT answer the question. Do NOT include any intro, explanation, or quotes. "
        "Respond with ONLY the rewritten search terms."
    )
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Conversational query: \"{query}\"\nOptimized search terms:"}
        ],
        temperature=0.0,
        max_tokens=40
    )
    rewritten = response.choices[0].message.content.strip()
    # Strip wrapping quotes if any
    rewritten = re.sub(r'^["\']|["\']$', '', rewritten)
    return rewritten

def execute_mock_rewrite(query: str) -> str:
    """
    Rule-based local query rewriter for mock/offline fallback.
    Strips common conversational prefixes and question words.
    """
    cleaned = query.lower().strip()
    
    # Common question prefixes to strip
    prefixes = [
        r"^what is the\b", r"^what did the\b", r"^what does the\b", r"^what did\b", r"^what does\b", r"^what\b",
        r"^how much was the\b", r"^how much was\b", r"^how much\b",
        r"^when was the\b", r"^when was\b", r"^when did\b", r"^when\b",
        r"^where is the\b", r"^where was the\b", r"^where\b",
        r"^can you tell me what\b", r"^can you tell me about\b", r"^can you tell me\b",
        r"^tell me about\b", r"^show me the\b", r"^search for\b", r"^find\b"
    ]
    
    for prefix in prefixes:
        cleaned = re.sub(prefix, "", cleaned).strip()
        
    # Strip question marks and punctuation
    cleaned = re.sub(r'[?.\!,:;"]', "", cleaned).strip()
    
    # If the cleanup resulted in empty string, return the original query
    if not cleaned:
        return query
        
    return cleaned

def rewrite_query(query: str) -> str:
    """
    Rewrite conversational query into optimized search terms.
    Uses LLM rewrite if key is present, falls back to offline rule-based rewriter.
    """
    if not query or not query.strip():
        return query
        
    if settings.OPENAI_API_KEY:
        try:
            rewritten = execute_live_rewrite(query)
            logger.info(f"LLM Query Rewriter: '{query}' -> '{rewritten}'")
            return rewritten
        except Exception as e:
            logger.error(f"LLM Query Rewrite failed, falling back to local mock rewriter. Error: {str(e)}")
            
    # Mock/Offline/Fallback path
    rewritten = execute_mock_rewrite(query)
    logger.info(f"Local Query Rewriter: '{query}' -> '{rewritten}'")
    return rewritten
