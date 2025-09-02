from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class PageWidget(BaseModel):
    page_id: str
    widget_id: str
    position: int

class PageWidgetResponse(BaseModel):
    relation_id: str
    page_id: str
    widget_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/page_widget", response_model=PageWidgetResponse)
async def create_page_widget(page_widget: PageWidget, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        page_widget_dict = page_widget.model_dump()
        page_widget_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        page_widget_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.page_widget.insert_one(page_widget_dict)
        page_widget_dict["relation_id"] = str(result.inserted_id)
        return PageWidgetResponse(**page_widget_dict)

@router.get("/api/internal/mongodb/relation/page_widget/{relation_id}", response_model=PageWidgetResponse)
async def get_page_widget(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        page_widget = await db.page_widget.find_one({"_id": ObjectId(relation_id)})
        if page_widget:
            page_widget["relation_id"] = str(page_widget["_id"])
            return PageWidgetResponse(**page_widget)
        raise HTTPException(status_code=404, detail="Page-Widget relation not found")

@router.put("/api/internal/mongodb/relation/page_widget/{relation_id}", response_model=PageWidgetResponse)
async def update_page_widget(relation_id: str, page_widget: PageWidget, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        page_widget_dict = page_widget.model_dump()
        result = await db.page_widget.update_one({"_id": ObjectId(relation_id)}, {"$set": page_widget_dict})
        if result.modified_count == 1:
            page_widget = await db.page_widget.find_one({"_id": ObjectId(relation_id)})
            page_widget["relation_id"] = str(page_widget["_id"])
            return PageWidgetResponse(**page_widget)
        raise HTTPException(status_code=404, detail="Page-Widget relation not found")

@router.delete("/api/internal/mongodb/relation/page_widget/{relation_id}", response_model=dict)
async def delete_page_widget(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.page_widget.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Page-Widget relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Page-Widget relation not found")
