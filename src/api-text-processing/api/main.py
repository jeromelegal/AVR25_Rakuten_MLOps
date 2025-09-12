from api.config.config import settings
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def read_root():
    return {"message": f"Text processing API {settings.SERVICE_VERSION}"}
