from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class DirectoryDocument(BaseModel):
    directory_id: str
    document_id: str
    position: int

class DirectoryDocumentResponse(BaseModel):
    relation_id: str
    directory_id: str
    document_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/directory_document", response_model=DirectoryDocumentResponse)
async def create_directory_document(directory_document: DirectoryDocument, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory_document_dict = directory_document.model_dump()
        directory_document_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        directory_document_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.directory_document.insert_one(directory_document_dict)
        directory_document_dict["relation_id"] = str(result.inserted_id)
        return DirectoryDocumentResponse(**directory_document_dict)

@router.get("/api/internal/mongodb/relation/directory_document/{relation_id}", response_model=DirectoryDocumentResponse)
async def get_directory_document(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory_document = await db.directory_document.find_one({"_id": ObjectId(relation_id)})
        if directory_document:
            directory_document["relation_id"] = str(directory_document["_id"])
            return DirectoryDocumentResponse(**directory_document)
        raise HTTPException(status_code=404, detail="Directory-Document relation not found")

@router.put("/api/internal/mongodb/relation/directory_document/{relation_id}", response_model=DirectoryDocumentResponse)
async def update_directory_document(relation_id: str, directory_document: DirectoryDocument, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory_document_dict = directory_document.model_dump()
        result = await db.directory_document.update_one({"_id": ObjectId(relation_id)}, {"$set": directory_document_dict})
        if result.modified_count == 1:
            directory_document = await db.directory_document.find_one({"_id": ObjectId(relation_id)})
            directory_document["relation_id"] = str(directory_document["_id"])
            return DirectoryDocumentResponse(**directory_document)
        raise HTTPException(status_code=404, detail="Directory-Document relation not found")

@router.delete("/api/internal/mongodb/relation/directory_document/{relation_id}", response_model=dict)
async def delete_directory_document(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.directory_document.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Directory-Document relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Directory-Document relation not found")
