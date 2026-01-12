from fastapi import APIRouter
from app.api.v1.endpoints import generate

api_router = APIRouter()
api_router.include_router(generate.router, prefix="/generate", tags=["generate"])
