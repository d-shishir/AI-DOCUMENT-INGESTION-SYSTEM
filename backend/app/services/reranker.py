import logging
import re
from ..config import settings

logger = logging.getLogger(__name__)

def compute_lexical_score(query: str, text: str) -> float:
    """
    Computes a simple term frequency match score between the query and text.
    Returns a normalized float score between 0.0 and 1.0.
    """
    query_terms = set(re.findall(r'\b\w{3,15}\b', query.lower()))
    # Remove standard stop words
    stop_words = {"what", "when", "where", "how", "who", "why", "whom", "which", "this", "that", "the", "for", "are", "you", "and", "document"}
    keywords = query_terms - stop_words
    
    if not keywords:
        keywords = query_terms
        
    if not keywords:
        return 0.0
        
    text_lower = text.lower()
    matches = 0
    
    # Calculate term matches with extra weighting for adjacent terms
    for term in keywords:
        # Match exact word boundaries
        term_matches = len(re.findall(r'\b' + re.escape(term) + r'\b', text_lower))
        if term_matches > 0:
            matches += min(term_matches, 3)  # cap term frequency contribution to avoid keyword stuffing bias
            
    # Normalize score
    max_possible_score = len(keywords) * 3
    if max_possible_score == 0:
        return 0.0
        
    lexical_score = matches / max_possible_score
    return min(lexical_score, 1.0)

def rerank_chunks(query: str, chunks: list[dict], top_k: int = None) -> list[dict]:
    """
    Reranks chunks based on a hybrid formula:
    score = (0.7 * semantic_similarity) + (0.3 * lexical_score)
    """
    if top_k is None:
        top_k = settings.RERANK_TOP_K
        
    if not chunks:
        return []
        
    reranked = []
    
    for chunk in chunks:
        # Cosine similarity is already between 0.0 and 1.0
        semantic_score = chunk.get("similarity", 0.0)
        
        # Calculate keyword match score
        lexical_score = compute_lexical_score(query, chunk["content"])
        
        # Hybrid formula
        hybrid_score = (0.7 * semantic_score) + (0.3 * lexical_score)
        
        # Create a new copy of the chunk with updated score
        updated_chunk = chunk.copy()
        updated_chunk["rerank_score"] = float(hybrid_score)
        updated_chunk["lexical_score"] = float(lexical_score)
        reranked.append(updated_chunk)
        
    # Sort chunks by hybrid rerank_score descending
    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    logger.info(f"Reranker: processed {len(chunks)} chunks, returning top {min(len(reranked), top_k)} sorted by hybrid score.")
    return reranked[:top_k]
