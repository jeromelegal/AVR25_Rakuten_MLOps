from api.config.config import SERVICE_VERSION
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def read_root():
    return {"message": f"Minio API {SERVICE_VERSION}"}
