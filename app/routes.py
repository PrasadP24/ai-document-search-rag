import os
from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.rag import ask_question, clear_vectorstore, create_vectorstore, list_indexed_documents
from app.utils import SUPPORTED_EXTENSIONS, extract_documents

router = APIRouter()

UPLOAD_DIR = "data"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    mode: Literal["search", "chat"] = "chat"
    source: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    result = await _index_files([file])
    return {
        "message": "File uploaded and indexed successfully",
        **result,
    }


@router.post("/upload/multiple")
async def upload_multiple_files(files: list[UploadFile] = File(...)):
    result = await _index_files(files)
    return {
        "message": "Files uploaded and indexed successfully",
        **result,
    }


@router.get("/ask")
def ask(
    question: str,
    mode: Literal["search", "chat"] = Query("search", description="Use 'search' for concise facts or 'chat' for conversational answers."),
    source: str | None = Query(None, description="Optional exact filename to search within one uploaded document."),
):
    result = ask_question(question=question, mode=mode, source=source)
    return {"question": question, **result}


@router.post("/chat")
def chat(request: ChatRequest):
    result = ask_question(
        question=request.question,
        mode=request.mode,
        source=request.source,
        history=[message.model_dump() for message in request.history],
    )
    return {"question": request.question, **result}


@router.get("/documents")
def documents():
    return {"documents": list_indexed_documents()}


@router.delete("/documents")
def delete_document(
    source: str = Query(..., description="Exact filename to delete, for example resume.pdf."),
):
    safe_name = os.path.basename(source)
    if safe_name != source:
        raise HTTPException(status_code=400, detail="Use only the filename, not a path.")

    file_path = os.path.join(UPLOAD_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{safe_name}' was not found.")

    os.remove(file_path)
    rebuild_result = _rebuild_index_from_uploads()

    return {
        "message": "Document deleted successfully",
        "deleted": safe_name,
        **rebuild_result,
    }


async def _index_files(files: list[UploadFile]) -> dict:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    indexed_files = []
    all_documents = []

    for file in files:
        if not file.filename:
            continue

        safe_name = os.path.basename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        with open(file_path, "wb") as destination:
            destination.write(await file.read())

        documents = extract_documents(file_path, safe_name)
        all_documents.extend(documents)
        indexed_files.append(
            {
                "filename": safe_name,
                "documents": len(documents),
            }
        )

    if not all_documents:
        raise HTTPException(status_code=400, detail="No readable supported files were uploaded.")

    create_vectorstore(all_documents, append=True)

    return {
        "files": indexed_files,
        "total_documents": len(all_documents),
    }


def _rebuild_index_from_uploads() -> dict:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    indexed_files = []
    all_documents = []

    for filename in sorted(os.listdir(UPLOAD_DIR)):
        extension = os.path.splitext(filename)[1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            continue

        file_path = os.path.join(UPLOAD_DIR, filename)
        documents = extract_documents(file_path, filename)
        all_documents.extend(documents)
        indexed_files.append(
            {
                "filename": filename,
                "documents": len(documents),
            }
        )

    if not all_documents:
        clear_vectorstore()
        return {
            "remaining_files": [],
            "total_documents": 0,
        }

    create_vectorstore(all_documents, append=False)

    return {
        "remaining_files": indexed_files,
        "total_documents": len(all_documents),
    }
