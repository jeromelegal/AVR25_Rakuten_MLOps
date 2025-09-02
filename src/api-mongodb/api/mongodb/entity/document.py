from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class Document(BaseModel):
    name: str
    type: str
    content: str
    variables: dict
    path: str

class DocumentResponse(BaseModel):
    document_id: str
    name: str
    type: str
    content: str
    variables: dict
    path: str
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/document", response_model=DocumentResponse)
async def create_document(document: Document, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        document_dict = document.model_dump()
        document_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        document_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.documents.insert_one(document_dict)
        document_dict["document_id"] = str(result.inserted_id)
        return DocumentResponse(**document_dict)

@router.get("/api/internal/mongodb/entity/document/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        document = await db.documents.find_one({"_id": ObjectId(document_id)})
        if document:
            document["document_id"] = str(document["_id"])
            return DocumentResponse(**document)
        raise HTTPException(status_code=404, detail="Document not found")

@router.put("/api/internal/mongodb/entity/document/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, document: Document, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        document_dict = document.model_dump()
        result = await db.documents.update_one({"_id": ObjectId(document_id)}, {"$set": document_dict})
        if result.modified_count == 1:
            document = await db.documents.find_one({"_id": ObjectId(document_id)})
            document["document_id"] = str(document["_id"])
            return DocumentResponse(**document)
        raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/api/internal/mongodb/entity/document/{document_id}", response_model=dict)
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.documents.delete_one({"_id": ObjectId(document_id)})
        if result.deleted_count == 1:
            return {"message": "Document deleted successfully"}
        raise HTTPException(status_code=404, detail="Document not found")
