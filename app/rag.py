import os
import pickle
import re
import shutil
from typing import Literal

from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

VECTOR_DB_PATH = "vectorstore/db"
LLM_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
LLM_MODEL = os.getenv("LM_STUDIO_MODEL", "qwen2.5-coder-1.5b-instruct")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "180"))
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "6"))
RERANK_CANDIDATES = int(os.getenv("RERANK_CANDIDATES", "12"))
HF_HUB_OFFLINE = os.getenv("HF_HUB_OFFLINE", "0") == "1"

_embedding_model: HuggingFaceEmbeddings | None = None


def create_vectorstore(documents: list[Document], append: bool = True) -> FAISS:
    chunks = _split_documents(documents)

    if append and _vectorstore_exists():
        db = load_vectorstore()
        db.add_documents(chunks)
    else:
        db = FAISS.from_documents(chunks, _embeddings())

    os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
    db.save_local(VECTOR_DB_PATH)

    return db


def load_vectorstore() -> FAISS:
    if not _vectorstore_exists():
        raise HTTPException(
            status_code=400,
            detail="No document has been uploaded and indexed yet.",
        )

    return FAISS.load_local(
        VECTOR_DB_PATH,
        _embeddings(),
        allow_dangerous_deserialization=True,
    )


def clear_vectorstore() -> None:
    if os.path.isdir(VECTOR_DB_PATH):
        shutil.rmtree(VECTOR_DB_PATH)
    elif os.path.exists(VECTOR_DB_PATH):
        os.remove(VECTOR_DB_PATH)


def ask_question(
    question: str,
    mode: Literal["search", "chat"] = "search",
    source: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    db = load_vectorstore()
    docs = _retrieve_documents(db, question, source)

    if not docs:
        return {
            "answer": "Not found in document.",
            "sources": [],
            "mode": mode,
        }

    context = _format_context(docs)
    try:
        response = _llm().invoke(_build_prompt(question, context, mode, history))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"LLM server is unavailable at {LLM_BASE_URL}. Start LM Studio or update LM_STUDIO_BASE_URL.",
        ) from exc

    return {
        "answer": response.content.strip(),
        "sources": _format_sources(docs),
        "mode": mode,
    }


def list_indexed_documents() -> list[dict]:
    if not _vectorstore_exists():
        return []

    docstore_documents = _load_saved_documents()
    documents: dict[str, dict] = {}

    for doc in docstore_documents:
        source = doc.metadata.get("source", "Unknown")
        if source not in documents:
            documents[source] = {
                "source": source,
                "file_type": doc.metadata.get("file_type"),
                "chunks": 0,
            }
        documents[source]["chunks"] += 1

    return sorted(documents.values(), key=lambda item: item["source"].lower())


def _load_saved_documents() -> list[Document]:
    index_metadata_path = os.path.join(VECTOR_DB_PATH, "index.pkl")
    if not os.path.exists(index_metadata_path):
        return list(load_vectorstore().docstore._dict.values())

    with open(index_metadata_path, "rb") as file:
        docstore, _ = pickle.load(file)

    return list(docstore._dict.values())


def _split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n# ", "\n## ", "\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks, start=1):
        chunk.metadata["chunk"] = index

    return chunks


def _retrieve_documents(db: FAISS, question: str, source: str | None) -> list[Document]:
    search_kwargs = {"k": max(RETRIEVER_K, RERANK_CANDIDATES)}
    if source:
        search_kwargs["filter"] = {"source": source}

    retriever = db.as_retriever(search_kwargs=search_kwargs)
    docs = retriever.invoke(question)

    return _rerank_documents(question, docs)[:RETRIEVER_K]


def _rerank_documents(question: str, docs: list[Document]) -> list[Document]:
    query_terms = _tokenize(question)
    if not query_terms:
        return docs

    scored_docs = []
    for vector_rank, doc in enumerate(docs):
        document_terms = _tokenize(doc.page_content)
        keyword_score = len(query_terms.intersection(document_terms))
        vector_score = 1 / (vector_rank + 1)
        scored_docs.append((keyword_score, vector_score, doc))

    scored_docs.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [doc for _, _, doc in scored_docs]


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9_@.+-]+", text.lower())
        if len(token) > 2
    }


def _format_context(docs: list[Document]) -> str:
    sections = []

    for index, doc in enumerate(docs, start=1):
        citation = _citation(doc.metadata)
        sections.append(f"[Source {index}: {citation}]\n{doc.page_content}")

    return "\n\n".join(sections)


def _build_prompt(question: str, context: str, mode: str, history: list[dict] | None = None) -> str:
    style = {
        "search": "Give a concise factual answer in bullet points.",
        "chat": "Answer conversationally, but stay grounded in the context.",
    }.get(mode, "Give a concise factual answer in bullet points.")

    conversation = _format_history(history or [])

    return f"""
You are an AI document assistant.

Use only the context below. If the answer is not in the context, say "Not found in document."
{style}
Include important names, dates, amounts, and contact details exactly as written when relevant.
When the user asks for contact details, look for phone numbers, email addresses, locations, and profile links.
Use the conversation history only to understand follow-up questions. Do not invent facts from chat history.

Conversation history:
{conversation}

Context:
{context}

Question:
{question}
"""


def _format_history(history: list[dict], max_messages: int = 8) -> str:
    if not history:
        return "No previous conversation."

    formatted_messages = []
    for message in history[-max_messages:]:
        role = message.get("role", "user")
        content = str(message.get("content", "")).strip()
        if content:
            formatted_messages.append(f"{role}: {content}")

    return "\n".join(formatted_messages) if formatted_messages else "No previous conversation."


def _format_sources(docs: list[Document]) -> list[dict]:
    sources = []
    seen = set()

    for doc in docs:
        metadata = doc.metadata
        key = (
            metadata.get("source"),
            metadata.get("page"),
            metadata.get("sheet"),
            metadata.get("row"),
            metadata.get("chunk"),
        )
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "source": metadata.get("source"),
                "page": metadata.get("page"),
                "sheet": metadata.get("sheet"),
                "row": metadata.get("row"),
                "chunk": metadata.get("chunk"),
                "preview": doc.page_content[:220],
            }
        )

    return sources


def _citation(metadata: dict) -> str:
    parts = [metadata.get("source", "Unknown source")]

    if metadata.get("page"):
        parts.append(f"page {metadata['page']}")
    if metadata.get("sheet"):
        parts.append(f"sheet {metadata['sheet']}")
    if metadata.get("row"):
        parts.append(f"row {metadata['row']}")
    if metadata.get("chunk"):
        parts.append(f"chunk {metadata['chunk']}")

    return ", ".join(str(part) for part in parts)


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=LLM_BASE_URL,
        api_key=os.getenv("LM_STUDIO_API_KEY", "not-needed"),
        model=LLM_MODEL,
        temperature=0,
    )


def _embeddings() -> HuggingFaceEmbeddings:
    global _embedding_model

    if _embedding_model is None:
        try:
            _embedding_model = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"local_files_only": HF_HUB_OFFLINE},
            )
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="Embedding model is unavailable. Check internet access or set HF_HUB_OFFLINE=1 after the model is cached.",
            ) from exc

    return _embedding_model


def _vectorstore_exists() -> bool:
    return os.path.exists(f"{VECTOR_DB_PATH}.faiss") or os.path.exists(
        os.path.join(VECTOR_DB_PATH, "index.faiss")
    )
