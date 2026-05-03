# AI Document Search API (RAG)

AI-powered document search system built with FastAPI, FAISS, LangChain, local embeddings, and an OpenAI-compatible local LLM through LM Studio.

## Highlights

- Streamlit product UI for uploading documents, chatting, viewing sources, and deleting indexed files
- Multi-format ingestion: PDF, DOCX, TXT, CSV, XLSX, and XLS
- Multi-document search across all uploaded files
- Source-based answers with filename, page, sheet, row, chunk, and preview citations
- CSV/Excel table understanding with row-level indexing and numeric column totals
- Hybrid retrieval with vector search plus keyword-aware reranking
- Search mode for concise factual answers
- Chat mode for conversational answers grounded in uploaded documents
- Chat memory for follow-up questions in the Streamlit UI
- Local inference through LM Studio for cost-efficient private document Q&A
- FAISS vector search with local HuggingFace sentence-transformer embeddings
- Dockerized backend and UI for easier deployment

## Resume Summary

Built an AI-powered document search system (RAG) with a Streamlit UI, FastAPI backend, and multi-format ingestion pipeline supporting PDF, DOCX, CSV, Excel, and TXT. Implemented hybrid retrieval using FAISS plus keyword-aware reranking, source-based answers, chat memory, structured responses, multi-document retrieval, document deletion with index rebuilding, request logging, Docker deployment, and local OpenAI-compatible inference through LM Studio.

## Tech Stack

- FastAPI
- LangChain
- FAISS
- HuggingFace sentence-transformers
- LM Studio / OpenAI-compatible chat API
- pypdf
- python-docx
- pandas
- openpyxl
- Streamlit
- Docker

## Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file if you want to override the LM Studio defaults:

```env
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=qwen2.5-coder-1.5b-instruct
LM_STUDIO_API_KEY=not-needed
CHUNK_SIZE=1000
CHUNK_OVERLAP=180
RETRIEVER_K=6
RERANK_CANDIDATES=12
HF_HUB_OFFLINE=0
API_BASE_URL=http://127.0.0.1:8000
```

Start LM Studio with an OpenAI-compatible server on port `1234`, then run:

```powershell
uvicorn app.main:app --reload
```

In another terminal, start the UI:

```powershell
streamlit run streamlit_app.py
```

Open the product UI:

```text
http://127.0.0.1:8501
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Docker

Run the API and Streamlit UI together:

```powershell
docker compose up --build
```

Open:

```text
UI:  http://127.0.0.1:8501
API: http://127.0.0.1:8000/docs
```

## API Endpoints

### Health Check

```http
GET /health
```

### Upload One Document

```http
POST /upload
```

Supports `.pdf`, `.docx`, `.txt`, `.csv`, `.xlsx`, and `.xls`.

### Upload Multiple Documents

```http
POST /upload/multiple
```

Indexes all uploaded files into the same FAISS vector database.

### Ask A Question

```http
GET /ask?question=give me name and contact details
```

Optional parameters:

- `mode=search` for concise factual answers
- `mode=chat` for conversational answers
- `source=filename.pdf` to search only inside one uploaded document

Example:

```http
GET /ask?question=what is total revenue&mode=search&source=sales.xlsx
```

Response shape:

```json
{
  "question": "give me name and contact details",
  "answer": "- Prasad Babaso Patil\n- prasadpatil12029@gmail.com\n- +91 8147522808",
  "sources": [
    {
      "source": "Prasad_Babaso_Patil-Resume.pdf",
      "page": 1,
      "sheet": null,
      "row": null,
      "chunk": 1,
      "preview": "Prasad Babaso Patil..."
    }
  ],
  "mode": "search"
}
```

### Chat With Memory

```http
POST /chat
```

Request shape:

```json
{
  "question": "What about his phone number?",
  "mode": "chat",
  "source": "resume.pdf",
  "history": [
    {"role": "user", "content": "Who is this resume about?"},
    {"role": "assistant", "content": "The resume is about Prasad Babaso Patil."}
  ]
}
```

### List Indexed Documents

```http
GET /documents
```

Returns indexed filenames, file types, and chunk counts.

### Delete A Document

```http
DELETE /documents?source=filename.pdf
```

Deletes the selected uploaded file from `data/` and rebuilds the FAISS index from the remaining documents.

## Project Structure

```text
app/
  main.py      FastAPI app setup
  routes.py    Upload, ask, and document listing endpoints
  rag.py       Chunking, FAISS indexing, retrieval, prompts, citations
  utils.py     PDF, DOCX, TXT, CSV, and Excel extraction
streamlit_app.py  Product UI
data/          Uploaded files
vectorstore/   Local FAISS index
```

## Showcase Materials

- [Showcase checklist and demo script](docs/SHOWCASE.md)
- [Deployment notes](docs/DEPLOYMENT.md)
- [Interview story](docs/INTERVIEW_STORY.md)
- [Technical blog draft](docs/BLOG_DRAFT.md)

## Demo Plan

1. Start LM Studio and run the API plus Streamlit UI.
2. Upload a resume, PDF, or spreadsheet.
3. Ask factual questions in search mode.
4. Switch to chat mode for conversational follow-ups.
5. Expand sources to show filename, page, row, chunk, and preview citations.
6. Delete a document and show that the index updates.
