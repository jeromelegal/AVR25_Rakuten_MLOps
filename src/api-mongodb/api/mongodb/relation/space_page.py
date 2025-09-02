from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class SpacePage(BaseModel):
    space_id: str
    page_id: str
    position: int

class SpacePageResponse(BaseModel):
    relation_id: str
    space_id: str
    page_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/space_page", response_model=SpacePageResponse)
async def create_space_page(space_page: SpacePage, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_page_dict = space_page.model_dump()
        space_page_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        space_page_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.space_page.insert_one(space_page_dict)
        space_page_dict["relation_id"] = str(result.inserted_id)
        return SpacePageResponse(**space_page_dict)

@router.get("/api/internal/mongodb/relation/space_page/{relation_id}", response_model=SpacePageResponse)
async def get_space_page(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_page = await db.space_page.find_one({"_id": ObjectId(relation_id)})
        if space_page:
            space_page["relation_id"] = str(space_page["_id"])
            return SpacePageResponse(**space_page)
        raise HTTPException(status_code=404, detail="Space-Page relation not found")

@router.put("/api/internal/mongodb/relation/space_page/{relation_id}", response_model=SpacePageResponse)
async def update_space_page(relation_id: str, space_page: SpacePage, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_page_dict = space_page.model_dump()
        result = await db.space_page.update_one({"_id": ObjectId(relation_id)}, {"$set": space_page_dict})
        if result.modified_count == 1:
            space_page = await db.space_page.find_one({"_id": ObjectId(relation_id)})
            space_page["relation_id"] = str(space_page["_id"])
            return SpacePageResponse(**space_page)
        raise HTTPException(status_code=404, detail="Space-Page relation not found")

@router.delete("/api/internal/mongodb/relation/space_page/{relation_id}", response_model=dict)
async def delete_space_page(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.space_page.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Space-Page relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Space-Page relation not found")
