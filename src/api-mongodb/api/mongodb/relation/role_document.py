from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleDocument(BaseModel):
    role_id: str
    document_id: str
    permissions: dict

class RoleDocumentResponse(BaseModel):
    relation_id: str
    role_id: str
    document_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_document", response_model=RoleDocumentResponse)
async def create_role_document(role_document: RoleDocument, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_document_dict = role_document.model_dump()
        role_document_dict["created_at"] = datetime.now(UTC).isoformat()
        role_document_dict["created_by"] = current_user["user_id"]
        result = await db.role_documents.insert_one(role_document_dict)
        role_document_dict["relation_id"] = str(result.inserted_id)
        return RoleDocumentResponse(**role_document_dict)

@router.get("/api/internal/mongodb/relation/role_document/{relation_id}", response_model=RoleDocumentResponse)
async def get_role_document(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_document = await db.role_documents.find_one({"_id": ObjectId(relation_id)})
        if role_document:
            role_document["relation_id"] = str(role_document["_id"])
            return RoleDocumentResponse(**role_document)
        raise HTTPException(status_code=404, detail="Role-Document relation not found")

@router.put("/api/internal/mongodb/relation/role_document/{relation_id}", response_model=RoleDocumentResponse)
async def update_role_document(relation_id: str, role_document: RoleDocument, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_document_dict = role_document.model_dump()
        result = await db.role_documents.update_one({"_id": ObjectId(relation_id)}, {"$set": role_document_dict})
        if result.modified_count == 1:
            role_document = await db.role_documents.find_one({"_id": ObjectId(relation_id)})
            role_document["relation_id"] = str(role_document["_id"])
            return RoleDocumentResponse(**role_document)
        raise HTTPException(status_code=404, detail="Role-Document relation not found")

@router.delete("/api/internal/mongodb/relation/role_document/{relation_id}", response_model=dict)
async def delete_role_document(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_documents.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Document relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Document relation not found")
