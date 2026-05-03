# Showcase Checklist

Use this when preparing the project for GitHub, LinkedIn, and interviews.

## GitHub README Assets

- Add a screenshot of the Streamlit UI after uploading a document.
- Add a screenshot of an answer with the Sources panel expanded.
- Add a screenshot of the document delete flow.
- Add a 2-3 minute demo video link near the top of the README.

Recommended folder:

```text
assets/
  ui-upload.png
  answer-sources.png
  delete-document.png
```

## Demo Video Script

1. Open the Streamlit UI.
2. Upload a resume, PDF, or spreadsheet.
3. Ask a factual question in search mode.
4. Expand Sources and show filename/page/row/chunk citations.
5. Switch to chat mode and ask a follow-up question.
6. Delete one document and show the indexed document list updating.
7. Close with the architecture: Streamlit UI, FastAPI API, FAISS, local embeddings, LM Studio.

## LinkedIn Post Draft

I built an AI-powered document search system using FastAPI, FAISS, LangChain, Streamlit, and LM Studio.

It supports PDF, DOCX, TXT, CSV, and Excel uploads, then answers questions with source citations. I also added multi-document retrieval, keyword-aware reranking, chat memory, document deletion with FAISS re-indexing, and a Streamlit UI for demos.

The project runs locally with LM Studio for privacy and cost-efficient inference.

Key learning: retrieval quality depends as much on chunking, metadata, and reranking as it does on the LLM.

Demo: <add video link>
GitHub: <add repo link>
