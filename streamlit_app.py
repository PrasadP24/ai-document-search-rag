import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
SUPPORTED_TYPES = ["pdf", "docx", "txt", "csv", "xlsx", "xls"]


def main() -> None:
    st.set_page_config(page_title="AI Document Search", layout="wide")
    st.title("AI Document Search")
    st.caption("Upload documents, ask grounded questions, and inspect sources.")

    with st.sidebar:
        _render_sidebar()

    _render_chat()


def _render_sidebar() -> None:
    st.header("Documents")
    uploaded_files = st.file_uploader(
        "Upload files",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
    )

    if st.button("Index Documents", type="primary", disabled=not uploaded_files):
        try:
            with st.spinner("Indexing documents..."):
                upload_documents(uploaded_files)
            st.success("Documents indexed")
            st.rerun()
        except requests.RequestException as exc:
            st.error(f"Upload failed: {_error_detail(exc)}")

    documents = get_documents()
    document_names = [document["source"] for document in documents]
    st.session_state.selected_source = st.selectbox("Search scope", ["All documents", *document_names])

    if documents:
        st.dataframe(documents, use_container_width=True, hide_index=True)

    delete_target = st.selectbox("Delete document", ["Select document", *document_names])
    if st.button("Delete Selected", disabled=delete_target == "Select document"):
        try:
            with st.spinner("Deleting and rebuilding index..."):
                delete_document(delete_target)
            st.success(f"Deleted {delete_target}")
            st.rerun()
        except requests.RequestException as exc:
            st.error(f"Delete failed: {_error_detail(exc)}")


def _render_chat() -> None:
    mode = st.radio("Mode", ["search", "chat"], horizontal=True)
    question = st.chat_input("Ask a question about your documents")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            _render_sources(message.get("sources", []))

    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                result = ask_question(
                    question,
                    mode,
                    None if st.session_state.selected_source == "All documents" else st.session_state.selected_source,
                    st.session_state.messages[:-1] if mode == "chat" else [],
                )

            st.markdown(result["answer"])
            _render_sources(result.get("sources", []))
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result.get("sources", []),
                }
            )
        except requests.RequestException as exc:
            st.error(f"Question failed: {_error_detail(exc)}")


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander("Sources"):
        for source in sources:
            label = f"**{source.get('source')}**"
            if source.get("page"):
                label += f" - page {source.get('page')}"
            if source.get("sheet"):
                label += f" - sheet {source.get('sheet')}"
            if source.get("row"):
                label += f" - row {source.get('row')}"

            st.markdown(label)
            st.caption(source.get("preview", ""))


def api_url(path: str) -> str:
    return f"{API_BASE_URL.rstrip('/')}{path}"


def get_documents() -> list[dict]:
    try:
        response = requests.get(api_url("/documents"), timeout=20)
        response.raise_for_status()
        return response.json().get("documents", [])
    except requests.RequestException as exc:
        st.error(f"Could not reach backend: {_error_detail(exc)}")
        return []


def upload_documents(files) -> None:
    payload = [
        ("files", (file.name, file.getvalue(), file.type or "application/octet-stream"))
        for file in files
    ]
    response = requests.post(api_url("/upload/multiple"), files=payload, timeout=180)
    response.raise_for_status()


def ask_question(question: str, mode: str, source: str | None, history: list[dict]) -> dict:
    payload = {
        "question": question,
        "mode": mode,
        "source": source,
        "history": [
            {"role": message["role"], "content": message["content"]}
            for message in history
            if message.get("role") in {"user", "assistant"} and message.get("content")
        ],
    }

    response = requests.post(api_url("/chat"), json=payload, timeout=300)
    response.raise_for_status()
    return response.json()


def delete_document(source: str) -> None:
    response = requests.delete(api_url("/documents"), params={"source": source}, timeout=180)
    response.raise_for_status()


def _error_detail(exc: requests.RequestException) -> str:
    if exc.response is None:
        return str(exc)

    try:
        return exc.response.json().get("detail", exc.response.text)
    except ValueError:
        return exc.response.text


if __name__ == "__main__":
    main()
