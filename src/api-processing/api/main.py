from typing import Annotated
from fastapi import APIRouter, Depends
from api.config.config import Settings, get_settings

router = APIRouter()


@router.get("/")
async def read_root(settings: Annotated[Settings, Depends(get_settings)]):
    return {"message": f"Processing API {settings.SERVICE_VERSION}"}
