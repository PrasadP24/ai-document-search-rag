# How I Built a Local RAG System with FastAPI, FAISS, and LM Studio

## Introduction

I built an AI-powered document search product that lets users upload documents and ask grounded questions over them. The project supports PDFs, DOCX, TXT, CSV, and Excel files, and returns answers with source citations.

The goal was to build something practical: a private local RAG system with a usable UI, not just a notebook.

## Architecture

```text
Streamlit UI
    |
FastAPI backend
    |
Document extraction
    |
Chunking + metadata
    |
HuggingFace embeddings
    |
FAISS vector store
    |
Hybrid retrieval + reranking
    |
LM Studio local LLM
```

## Key Decisions

I chose FastAPI because it is lightweight, easy to document with Swagger, and fits backend API work well.

I chose FAISS because it gives efficient local vector search without needing a cloud vector database.

I chose LM Studio because it exposes a local OpenAI-compatible API, which keeps document data private and avoids external inference cost.

## Retrieval Pipeline

The system extracts text and metadata from uploaded documents. For PDFs, it stores page numbers. For spreadsheets, it indexes row-level information and numeric totals. Chunks are embedded with a sentence-transformer model and stored in FAISS.

At query time, the system retrieves candidate chunks using vector search and then reranks them using keyword overlap. This improves accuracy for questions that contain exact names, fields, or numbers.

## Source Citations

Each answer returns citations with filename, page, sheet, row, chunk, and text preview. This makes the system easier to trust and debug.

## Chat Memory

The Streamlit UI stores recent messages and sends them to the backend chat endpoint. The prompt uses history only for understanding follow-up questions, while facts still come from retrieved document context.

## Challenges

One challenge was keeping the app local and private while still making it demoable. Another was handling file uploads cleanly across PDFs, Word files, text files, and spreadsheets.

I also had to make API errors readable. If LM Studio is not running, the API returns a clear message instead of a traceback.

## What I Would Add Next

- PDF highlight viewer
- User authentication and user-specific indexes
- Hosted inference option for public cloud demos
- Evaluation tests for retrieval quality
