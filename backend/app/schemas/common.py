"""
Shared Pydantic schemas used across multiple endpoints.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str