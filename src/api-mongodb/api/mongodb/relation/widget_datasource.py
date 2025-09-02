from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class WidgetDatasource(BaseModel):
    widget_id: str
    datasource_id: str
    position: int

class WidgetDatasourceResponse(BaseModel):
    relation_id: str
    widget_id: str
    datasource_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/widget_datasource", response_model=WidgetDatasourceResponse)
async def create_widget_datasource(widget_datasource: WidgetDatasource, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        widget_datasource_dict = widget_datasource.model_dump()
        widget_datasource_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        widget_datasource_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.widget_datasource.insert_one(widget_datasource_dict)
        widget_datasource_dict["relation_id"] = str(result.inserted_id)
        return WidgetDatasourceResponse(**widget_datasource_dict)

@router.get("/api/internal/mongodb/relation/widget_datasource/{relation_id}", response_model=WidgetDatasourceResponse)
async def get_widget_datasource(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        widget_datasource = await db.widget_datasource.find_one({"_id": ObjectId(relation_id)})
        if widget_datasource:
            widget_datasource["relation_id"] = str(widget_datasource["_id"])
            return WidgetDatasourceResponse(**widget_datasource)
        raise HTTPException(status_code=404, detail="Widget-Datasource relation not found")

@router.put("/api/internal/mongodb/relation/widget_datasource/{relation_id}", response_model=WidgetDatasourceResponse)
async def update_widget_datasource(relation_id: str, widget_datasource: WidgetDatasource, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        widget_datasource_dict = widget_datasource.model_dump()
        result = await db.widget_datasource.update_one({"_id": ObjectId(relation_id)}, {"$set": widget_datasource_dict})
        if result.modified_count == 1:
            widget_datasource = await db.widget_datasource.find_one({"_id": ObjectId(relation_id)})
            widget_datasource["relation_id"] = str(widget_datasource["_id"])
            return WidgetDatasourceResponse(**widget_datasource)
        raise HTTPException(status_code=404, detail="Widget-Datasource relation not found")

@router.delete("/api/internal/mongodb/relation/widget_datasource/{relation_id}", response_model=dict)
async def delete_widget_datasource(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.widget_datasource.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Widget-Datasource relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Widget-Datasource relation not found")
