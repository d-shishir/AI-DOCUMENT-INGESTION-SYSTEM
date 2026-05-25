# Prompt Builder Service for RAG Pipeline

SYSTEM_PROMPT = """
You are a highly precise document QA assistant. 
Your core task is to answer the user's question based ONLY on the provided document context chunks.

RULES:
1. Base your answer STRICTLY on the text provided in the CONTEXT block.
2. If the answer cannot be found in the provided CONTEXT, reply EXACTLY: "Not found in documents" - do not attempt to construct an answer, do not write explanations, and do not say anything else.
3. Be direct, clear, and concise. Do not write filler introductory text (such as "Based on the provided context...").
4. Do not make assumptions, expand details, or hallucinate beyond what is explicitly written.
"""

def build_context_block(chunks: list[dict]) -> str:
    """
    Formats the list of matched document chunks into a clean, numbered context string.
    """
    context_parts = []
    for idx, chunk in enumerate(chunks, 1):
        filename = chunk.get("filename", "Unknown Document")
        content = chunk.get("content", "").strip()
        context_parts.append(
            f"--- Context Chunk {idx} (Source File: {filename}) ---\n"
            f"{content}\n"
        )
    return "\n".join(context_parts)

def build_prompt_payload(query: str, chunks: list[dict]) -> tuple[str, str]:
    """
    Returns a tuple of (system_instruction, user_content) to be sent directly to the LLM.
    """
    context_text = build_context_block(chunks)
    
    user_content = (
        f"CONTEXT:\n"
        f"{context_text}\n"
        f"==================================================\n\n"
        f"QUESTION: {query}\n\n"
        f"Answer:"
    )
    
    return SYSTEM_PROMPT, user_content
