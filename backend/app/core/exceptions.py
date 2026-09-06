"""
Custom application-level exceptions.

Services/repositories raise these instead of raw HTTPExceptions, so business
logic doesn't need to know about FastAPI/HTTP at all — the API layer (via the
handler registered in main.py) converts them into HTTP responses.
"""


class AppError(Exception):
    """Base class for all application-raised errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource doesn't exist (or isn't visible to the caller)."""


class ForbiddenError(AppError):
    """Raised when the authenticated user isn't allowed to perform this action."""


class ConflictError(AppError):
    """Raised for things like duplicate report submissions."""