import logging
import time

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.routes import router

app = FastAPI(title="AI Document Search")

app.include_router(router)
logger = logging.getLogger("ai_doc_search")


@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "%s %s completed with %s in %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )
    _fix_file_upload_schema(openapi_schema)
    app.openapi_schema = openapi_schema

    return app.openapi_schema


def _fix_file_upload_schema(value):
    if isinstance(value, dict):
        if value.get("type") == "string" and value.get("contentMediaType") == "application/octet-stream":
            value.pop("contentMediaType", None)
            value["format"] = "binary"

        for child in value.values():
            _fix_file_upload_schema(child)
    elif isinstance(value, list):
        for item in value:
            _fix_file_upload_schema(item)


app.openapi = custom_openapi
