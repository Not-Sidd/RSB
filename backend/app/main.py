"""
Entry point for the Franchise Management API.

This is a Phase 1 placeholder that only proves the project, virtual
environment, and dependencies are wired up correctly. The real
application structure (routers, DB session, auth, RBAC dependencies)
is built out starting in Phase 3.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Franchise Management API",
    version="0.1.0",
    description="Backend for the multi-store/franchise management application.",
)


@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Basic liveness check used to confirm the server is running."""
    return {"status": "ok"}
