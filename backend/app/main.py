"""
Entry point for the Franchise Management API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.middleware.logging import RequestLoggingMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Backend for the multi-store/franchise management application.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

_ERROR_STATUS = {
    NotFoundError: 404,
    ForbiddenError: 403,
    ConflictError: 409,
}


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    status_code = _ERROR_STATUS.get(type(exc), 400)
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Basic liveness check used to confirm the server is running."""
    return {"status": "ok"}


app.include_router(api_router)