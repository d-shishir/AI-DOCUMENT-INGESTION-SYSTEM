import logging
import re
from openai import OpenAI
from sqlalchemy.orm import Session
from ..config import settings
from .embeddings import get_embedding
from .vector_store import search_similar_chunks
from .prompt_builder import build_prompt_payload

logger = logging.getLogger(__name__)

def execute_live_rag(system_prompt: str, user_content: str) -> str:
    """
    Sends the compiled context prompt payload to OpenAI.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content.strip()

def execute_mock_rag(query: str, chunks: list[dict]) -> str:
    """
    Simulates a grounded RAG engine using keyword similarity in Python.
    Strictly answers ONLY using sentences from chunks that overlap with query terms.
    If no overlaps are found, replies "Not found in documents".
    """
    logger.info("Executing Q&A in MOCK RAG mode.")
    
    # Extract keywords from query
    query_words = set(re.findall(r'\b\w{3,12}\b', query.lower()))
    # Remove common filler words
    fillers = {"what", "when", "where", "how", "who", "why", "whom", "which", "this", "that", "the", "for", "are", "you", "and", "invoice", "document"}
    keywords = query_words - fillers
    
    if not keywords:
        keywords = query_words
        
    matched_sentences = []
    
    for chunk in chunks:
        content = chunk["content"]
        # Split chunk into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        for sentence in sentences:
            sentence_words = set(re.findall(r'\b\w{3,12}\b', sentence.lower()))
            # If the sentence matches any keyword
            if keywords & sentence_words:
                cleaned_sentence = sentence.strip()
                if cleaned_sentence and cleaned_sentence not in matched_sentences:
                    matched_sentences.append(cleaned_sentence)
                    
    if matched_sentences:
        # Return matched sentences assembled as a paragraph
        return " ".join(matched_sentences[:3])
    else:
        return "Not found in documents"

def ask_question_rag(db: Session, query: str, limit: int = 4) -> dict:
    """
    Full RAG Pipeline Orchestrator:
    1. Vectorize user query.
    2. Query database for similar chunks.
    3. Construct strict prompt payload.
    4. Call LLM (OpenAI) or Mock fallback.
    5. Return grounded answer and document references.
    """
    # Verify we have vectorized chunks to search
    try:
        # Generate query embedding
        query_vector = get_embedding(query)
        
        # Retrieve similar chunks
        results = search_similar_chunks(db, query_vector, limit=limit)
        
        if not results:
            return {
                "answer": "Not found in documents",
                "sources": []
            }
            
        # Format chunks for prompt builder
        formatted_chunks = [
            {"filename": r["filename"], "content": r["content"]}
            for r in results
        ]
        
        # Build prompt payload
        system_prompt, user_content = build_prompt_payload(query, formatted_chunks)
        
        # Call LLM or mock fallback
        if settings.OPENAI_API_KEY:
            try:
                answer = execute_live_rag(system_prompt, user_content)
            except Exception as e:
                logger.error(f"Live RAG query failed. Falling back to Mock RAG. Error: {str(e)}")
                answer = execute_mock_rag(query, results)
        else:
            answer = execute_mock_rag(query, results)
            
        # Filter sources based on answers
        # If the LLM declared "Not found in documents", we don't show source citations
        sources = []
        if "not found in documents" not in answer.lower():
            sources = [
                {
                    "document_id": r["document_id"],
                    "chunk_text": r["content"],
                    "score": r["similarity"],
                    "filename": r["filename"]
                }
                for r in results
            ]
            
        return {
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        logger.exception("RAG pipeline execution failed")
        raise e
