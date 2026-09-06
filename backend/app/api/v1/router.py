"""
Aggregates all /api/v1 routers into one. New resource routers (users,
stores, reports, ...) get included here as they're built in later phases —
main.py only ever needs to know about this one router.
"""

from fastapi import APIRouter

from app.api.v1 import system

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)