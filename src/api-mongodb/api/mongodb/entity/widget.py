from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class Widget(BaseModel):
    name: str
    type: str
    configuration: dict

class WidgetResponse(BaseModel):
    widget_id: str
    name: str
    type: str
    configuration: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/widget", response_model=WidgetResponse)
async def create_widget(widget: Widget, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        widget_dict = widget.model_dump()
        widget_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        widget_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.widgets.insert_one(widget_dict)
        widget_dict["widget_id"] = str(result.inserted_id)
        return WidgetResponse(**widget_dict)

@router.get("/api/internal/mongodb/entity/widget/{widget_id}", response_model=WidgetResponse)
async def get_widget(widget_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        widget = await db.widgets.find_one({"_id": ObjectId(widget_id)})
        if widget:
            widget["widget_id"] = str(widget["_id"])
            return WidgetResponse(**widget)
        raise HTTPException(status_code=404, detail="Widget not found")

@router.put("/api/internal/mongodb/entity/widget/{widget_id}", response_model=WidgetResponse)
async def update_widget(widget_id: str, widget: Widget, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        widget_dict = widget.model_dump()
        result = await db.widgets.update_one({"_id": ObjectId(widget_id)}, {"$set": widget_dict})
        if result.modified_count == 1:
            widget = await db.widgets.find_one({"_id": ObjectId(widget_id)})
            widget["widget_id"] = str(widget["_id"])
            return WidgetResponse(**widget)
        raise HTTPException(status_code=404, detail="Widget not found")

@router.delete("/api/internal/mongodb/entity/widget/{widget_id}", response_model=dict)
async def delete_widget(widget_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.widgets.delete_one({"_id": ObjectId(widget_id)})
        if result.deleted_count == 1:
            return {"message": "Widget deleted successfully"}
        raise HTTPException(status_code=404, detail="Widget not found")
