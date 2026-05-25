import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..models import Document

logger = logging.getLogger(__name__)

def save_document_chunks(db: Session, document_id: str, chunks: list[dict], embeddings: list[list[float]]) -> None:
    """
    Deletes any existing chunks for the given document, and saves the new chunks
    along with their generated high-dimensional vector embeddings.
    """
    try:
        # Delete existing chunks first to prevent duplication
        delete_query = text("DELETE FROM document_chunks WHERE document_id = :doc_id")
        db.execute(delete_query, {"doc_id": document_id})
        
        # Insert chunks in batch
        insert_query = text("""
            INSERT INTO document_chunks (document_id, chunk_index, content, embedding)
            VALUES (:doc_id, :idx, :content, CAST(:emb AS vector))
        """)
        
        for idx, chunk in enumerate(chunks):
            vector_str = f"[{','.join(str(v) for v in embeddings[idx])}]"
            db.execute(insert_query, {
                "doc_id": document_id,
                "idx": chunk["chunk_index"],
                "content": chunk["chunk_text"],
                "emb": vector_str
            })
            
        db.commit()
        logger.info(f"Successfully chunked and saved vector embeddings in pgvector for document: {document_id}")
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to save document chunks into vector store: {str(e)}")
        raise e

def search_similar_chunks(db: Session, query_vector: list[float], limit: int = 5) -> list[dict]:
    """
    Performs a native pgvector similarity search against document chunks using
    the `<=>` cosine distance operator (where 1 - distance equals similarity).
    """
    try:
        vector_str = f"[{','.join(str(v) for v in query_vector)}]"
        search_query = text("""
            SELECT 
                c.content, 
                c.chunk_index, 
                c.document_id, 
                d.filename,
                1 - (c.embedding <=> CAST(:emb AS vector)) AS similarity
            FROM document_chunks c
            JOIN documents d ON c.document_id = d.id
            ORDER BY c.embedding <=> CAST(:emb AS vector)
            LIMIT :limit
        """)
        
        result = db.execute(search_query, {
            "emb": vector_str,
            "limit": limit
        })
        
        results_list = []
        for row in result:
            results_list.append({
                "content": row.content,
                "chunk_index": row.chunk_index,
                "document_id": str(row.document_id),
                "filename": row.filename,
                "similarity": float(row.similarity)
            })
            
        return results_list
        
    except Exception as e:
        logger.exception(f"Semantic similarity query execution failed: {str(e)}")
        raise e
