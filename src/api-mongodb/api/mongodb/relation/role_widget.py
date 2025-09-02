from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleWidget(BaseModel):
    role_id: str
    widget_id: str
    permissions: dict

class RoleWidgetResponse(BaseModel):
    relation_id: str
    role_id: str
    widget_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_widget", response_model=RoleWidgetResponse)
async def create_role_widget(role_widget: RoleWidget, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_widget_dict = role_widget.model_dump()
        role_widget_dict["created_at"] = datetime.now(UTC).isoformat()
        role_widget_dict["created_by"] = current_user["user_id"]
        result = await db.role_widgets.insert_one(role_widget_dict)
        role_widget_dict["relation_id"] = str(result.inserted_id)
        return RoleWidgetResponse(**role_widget_dict)

@router.get("/api/internal/mongodb/relation/role_widget/{relation_id}", response_model=RoleWidgetResponse)
async def get_role_widget(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_widget = await db.role_widgets.find_one({"_id": ObjectId(relation_id)})
        if role_widget:
            role_widget["relation_id"] = str(role_widget["_id"])
            return RoleWidgetResponse(**role_widget)
        raise HTTPException(status_code=404, detail="Role-Widget relation not found")

@router.put("/api/internal/mongodb/relation/role_widget/{relation_id}", response_model=RoleWidgetResponse)
async def update_role_widget(relation_id: str, role_widget: RoleWidget, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_widget_dict = role_widget.model_dump()
        result = await db.role_widgets.update_one({"_id": ObjectId(relation_id)}, {"$set": role_widget_dict})
        if result.modified_count == 1:
            role_widget = await db.role_widgets.find_one({"_id": ObjectId(relation_id)})
            role_widget["relation_id"] = str(role_widget["_id"])
            return RoleWidgetResponse(**role_widget)
        raise HTTPException(status_code=404, detail="Role-Widget relation not found")

@router.delete("/api/internal/mongodb/relation/role_widget/{relation_id}", response_model=dict)
async def delete_role_widget(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_widgets.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Widget relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Widget relation not found")
