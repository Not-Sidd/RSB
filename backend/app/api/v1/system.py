"""
System-level endpoints: liveness and DB connectivity checks.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["system"])


@router.get("/ping")
def ping(db: Session = Depends(get_db)) -> dict:
    """
    Proves the full chain works: FastAPI -> DB session dependency ->
    SQLAlchemy -> MySQL. Returns the count of organizations so it's
    also a trivial sanity check that the schema is reachable.
    """
    result = db.execute(text("SELECT COUNT(*) FROM organizations"))
    count = result.scalar_one()
    return {"status": "ok", "organizations_count": count}