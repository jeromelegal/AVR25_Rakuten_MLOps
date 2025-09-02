from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class Page(BaseModel):
    name: str
    content: str

class PageResponse(BaseModel):
    page_id: str
    name: str
    content: str
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/page", response_model=PageResponse)
async def create_page(page: Page, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        page_dict = page.model_dump()
        page_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        page_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.pages.insert_one(page_dict)
        page_dict["page_id"] = str(result.inserted_id)
        return PageResponse(**page_dict)

@router.get("/api/internal/mongodb/entity/page/{page_id}", response_model=PageResponse)
async def get_page(page_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        page = await db.pages.find_one({"_id": ObjectId(page_id)})
        if page:
            page["page_id"] = str(page["_id"])
            return PageResponse(**page)
        raise HTTPException(status_code=404, detail="Page not found")

@router.put("/api/internal/mongodb/entity/page/{page_id}", response_model=PageResponse)
async def update_page(page_id: str, page: Page, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        page_dict = page.model_dump()
        result = await db.pages.update_one({"_id": ObjectId(page_id)}, {"$set": page_dict})
        if result.modified_count == 1:
            page = await db.pages.find_one({"_id": ObjectId(page_id)})
            page["page_id"] = str(page["_id"])
            return PageResponse(**page)
        raise HTTPException(status_code=404, detail="Page not found")

@router.delete("/api/internal/mongodb/entity/page/{page_id}", response_model=dict)
async def delete_page(page_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.pages.delete_one({"_id": ObjectId(page_id)})
        if result.deleted_count == 1:
            return {"message": "Page deleted successfully"}
        raise HTTPException(status_code=404, detail="Page not found")
