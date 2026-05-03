# Interview Story

## Short Pitch

I built a local RAG document search product with a Streamlit UI and FastAPI backend. Users can upload PDFs, DOCX, TXT, CSV, and Excel files, ask questions, and get answers with source citations. Retrieval uses FAISS vector search with local HuggingFace embeddings plus keyword-aware reranking, and generation runs through LM Studio using an OpenAI-compatible API.

## Why RAG?

RAG lets the model answer from uploaded documents instead of relying on training data. That makes answers more grounded, easier to cite, and safer for private or frequently changing content.

## Why FAISS?

FAISS is fast, local, and simple to run without cloud infrastructure. It is a good fit for a private document search project where I want efficient semantic retrieval without paying for a hosted vector database.

## Why Local LLM / LM Studio?

LM Studio gives an OpenAI-compatible local server, so I can test RAG behavior without sending documents to an external API. It keeps data private and removes per-request inference cost.

## How Retrieval Works

1. Extract text and metadata from uploaded files.
2. Split documents into overlapping chunks.
3. Embed chunks using `all-MiniLM-L6-v2`.
4. Store embeddings and metadata in FAISS.
5. Retrieve candidate chunks for each question.
6. Rerank candidates with keyword overlap.
7. Send the best chunks to the LLM with a grounded prompt.
8. Return the answer plus source citations.

## Limitations

- Local LLM quality depends on the model running in LM Studio.
- FAISS storage is local, so cloud deployment needs persistent disk.
- Current chat memory is session-level in the UI, not user-authenticated persistent memory.
- Source previews are text snippets, not visual PDF highlights yet.

## Strong Resume Bullet

Built a local RAG document search product using FastAPI, Streamlit, FAISS, LangChain, HuggingFace embeddings, and LM Studio. Implemented multi-format ingestion, hybrid retrieval with keyword-aware reranking, chat memory, source citations, document deletion with index rebuilding, and Dockerized deployment support.
