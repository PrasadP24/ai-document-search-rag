# Deployment Notes

This project is designed for local private RAG with LM Studio. Cloud deployment needs one decision first: where the LLM will run.

## Option 1: Local Demo

Best for privacy-focused demos.

Run LM Studio locally, then start:

```powershell
.\venv\Scripts\python -m uvicorn app.main:app --reload
.\venv\Scripts\streamlit run streamlit_app.py
```

## Option 2: Docker Local Demo

```powershell
docker compose up --build
```

Open:

```text
UI:  http://127.0.0.1:8501
API: http://127.0.0.1:8000/docs
```

## Option 3: Cloud Demo

LM Studio runs on your machine, so it is not reachable from Render, Railway, or Streamlit Cloud by default.

For a public cloud demo, switch one of these:

- Use OpenAI-compatible hosted inference and set `LM_STUDIO_BASE_URL`.
- Use a hosted Ollama/HuggingFace/vLLM server with an OpenAI-compatible endpoint.
- Keep the project local and clearly label it: "Runs locally with LM Studio for privacy."

## Environment Variables

```env
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=qwen2.5-coder-1.5b-instruct
LM_STUDIO_API_KEY=not-needed
CHUNK_SIZE=1000
CHUNK_OVERLAP=180
RETRIEVER_K=6
RERANK_CANDIDATES=12
HF_HUB_OFFLINE=1
API_BASE_URL=http://127.0.0.1:8000
```

## Persistent Storage

Persist these folders in production:

```text
data/
vectorstore/
```

Without persistent storage, uploaded files and FAISS indexes will disappear when the container restarts.
