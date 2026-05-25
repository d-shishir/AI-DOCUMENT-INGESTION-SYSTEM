import re
import logging

logger = logging.getLogger(__name__)

def split_text_into_chunks(text: str, chunk_size: int = 600, overlap: int = 150) -> list[dict]:
    """
    Split text into chunks of roughly `chunk_size` characters,
    maintaining an overlap of `overlap` characters between consecutive chunks.
    It attempts to break at sentence boundaries (dots/newlines) rather than splitting mid-word.
    """
    if not text or not text.strip():
        return []
        
    chunks = []
    text_length = len(text)
    
    start = 0
    chunk_index = 0
    
    while start < text_length:
        # Determine initial chunk window
        end = min(start + chunk_size, text_length)
        
        # If we are not at the end of the text, try to find a natural break point (dot or newline)
        if end < text_length:
            # Look for a dot or newline in the last 15% of the chunk window
            search_window_start = max(start, end - int(chunk_size * 0.15))
            search_text = text[search_window_start:end]
            
            # Find last sentence-ending dot or paragraph newline
            match = list(re.finditer(r'\.|\n', search_text))
            if match:
                # Set end to be right after the dot or newline
                end = search_window_start + match[-1].end()
                
        chunk_text = text[start:end].strip()
        
        # Save chunk details if it contains actual content
        if chunk_text:
            chunks.append({
                "chunk_index": chunk_index,
                "chunk_text": chunk_text
            })
            chunk_index += 1
            
        if end >= text_length:
            break
            
        # Move the slide window forward, accounting for overlap
        start = max(start + 1, end - overlap)
        
    logger.info(f"Chunker completed: split input text ({text_length} chars) into {len(chunks)} segments.")
    return chunks
