# Day 04: Grounded RAG Chat Engine & Sources Tracker

## Completed Work

### 1. RAG Core Pipeline Backend
- Created prompt building service in `prompt_builder.py` defining strict system instructions and formatting context block schemas.
- Created `rag_pipeline.py` orchestrating the RAG flow: generating query vector embeds, fetching matched chunks via native pgvector searches, building context prompt payloads, and invoking OpenAI API chat completions.
- Implemented a keyword-based Mock RAG solver fallback to enable offline local query tests if no `OPENAI_API_KEY` is present.
- Exposed `POST /chat-with-documents` returning JSON objects with grounded answers and source citations.

### 2. Frontend Workspace Tabbed Console
- Created workspace tab structures inside `App.tsx` separating the dashboard into **Library Catalog**, **Semantic Search**, and **RAG Chat Assistant** views.
- Implemented a chat interface displaying user message bubbles, system thinking loaders, suggestions chips, and AI answers.
- Implemented expandable citation dropdown modules ("Sources & Citations") beneath bot replies, showing similarity scores, chunk snippets, and parent document filenames.
