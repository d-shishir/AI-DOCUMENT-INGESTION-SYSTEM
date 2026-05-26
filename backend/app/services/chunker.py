import re
import logging
from ..config import settings

logger = logging.getLogger(__name__)

def split_text_into_chunks(text: str, chunk_size: int = None, overlap: int = None) -> list[dict]:
    """
    Split text into semantic chunks of roughly `chunk_size` characters,
    maintaining an overlap of `overlap` characters between consecutive chunks.
    It attempts to break at paragraph breaks and sentence boundaries rather than splitting mid-word.
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if overlap is None:
        overlap = settings.CHUNK_OVERLAP

    if not text or not text.strip():
        return []
        
    # Split text into paragraphs based on blank lines or double newlines
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    chunk_index = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        para_len = len(para)
        
        # If a single paragraph is larger than the chunk size, split it into sentences
        if para_len > chunk_size:
            # Flush existing chunk accumulation
            if current_chunk:
                chunk_content = "\n\n".join(current_chunk)
                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_content
                })
                chunk_index += 1
                current_chunk = []
                current_length = 0
                
            # Process paragraph sentence by sentence
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                sentence_len = len(sentence)
                if current_length + sentence_len > chunk_size and current_chunk:
                    # Flush
                    chunk_content = " ".join(current_chunk)
                    chunks.append({
                        "chunk_index": chunk_index,
                        "chunk_text": chunk_content
                    })
                    chunk_index += 1
                    
                    # Carry over overlap
                    overlap_sentences = []
                    overlap_len = 0
                    for s in reversed(current_chunk):
                        if overlap_len + len(s) <= overlap:
                            overlap_sentences.insert(0, s)
                            overlap_len += len(s) + 1
                        else:
                            break
                    current_chunk = overlap_sentences
                    current_length = sum(len(s) for s in current_chunk) + len(current_chunk) - 1 if current_chunk else 0
                
                current_chunk.append(sentence)
                current_length += sentence_len + (1 if current_length > 0 else 0)
                
            continue

        # If adding this paragraph exceeds chunk size, flush the current chunk
        if current_length + para_len > chunk_size and current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunks.append({
                "chunk_index": chunk_index,
                "chunk_text": chunk_content
            })
            chunk_index += 1
            
            # Carry over overlap
            overlap_paras = []
            overlap_len = 0
            for p in reversed(current_chunk):
                if overlap_len + len(p) <= overlap:
                    overlap_paras.insert(0, p)
                    overlap_len += len(p) + 2
                else:
                    break
            current_chunk = overlap_paras
            current_length = sum(len(p) for p in current_chunk) + (len(current_chunk) - 1) * 2 if current_chunk else 0

        current_chunk.append(para)
        current_length += para_len + (2 if current_length > 0 else 0)

    # Flush any remaining content
    if current_chunk:
        chunk_content = "\n\n".join(current_chunk)
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_text": chunk_content
        })
        
    logger.info(f"Semantic chunker completed: split input text ({len(text)} chars) into {len(chunks)} segments (chunk_size={chunk_size}, overlap={overlap}).")
    return chunks
