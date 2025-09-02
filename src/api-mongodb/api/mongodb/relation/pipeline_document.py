from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class PipelineDocument(BaseModel):
    pipeline_id: str
    document_id: str
    position: int

class PipelineDocumentResponse(BaseModel):
    relation_id: str
    pipeline_id: str
    document_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/pipeline_document", response_model=PipelineDocumentResponse)
async def create_pipeline_document(pipeline_document: PipelineDocument, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_document_dict = pipeline_document.model_dump()
        pipeline_document_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        pipeline_document_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.pipeline_document.insert_one(pipeline_document_dict)
        pipeline_document_dict["relation_id"] = str(result.inserted_id)
        return PipelineDocumentResponse(**pipeline_document_dict)

@router.get("/api/internal/mongodb/relation/pipeline_document/{relation_id}", response_model=PipelineDocumentResponse)
async def get_pipeline_document(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_document = await db.pipeline_document.find_one({"_id": ObjectId(relation_id)})
        if pipeline_document:
            pipeline_document["relation_id"] = str(pipeline_document["_id"])
            return PipelineDocumentResponse(**pipeline_document)
        raise HTTPException(status_code=404, detail="Pipeline-Document relation not found")

@router.put("/api/internal/mongodb/relation/pipeline_document/{relation_id}", response_model=PipelineDocumentResponse)
async def update_pipeline_document(relation_id: str, pipeline_document: PipelineDocument, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_document_dict = pipeline_document.model_dump()
        result = await db.pipeline_document.update_one({"_id": ObjectId(relation_id)}, {"$set": pipeline_document_dict})
        if result.modified_count == 1:
            pipeline_document = await db.pipeline_document.find_one({"_id": ObjectId(relation_id)})
            pipeline_document["relation_id"] = str(pipeline_document["_id"])
            return PipelineDocumentResponse(**pipeline_document)
        raise HTTPException(status_code=404, detail="Pipeline-Document relation not found")

@router.delete("/api/internal/mongodb/relation/pipeline_document/{relation_id}", response_model=dict)
async def delete_pipeline_document(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.pipeline_document.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Pipeline-Document relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Pipeline-Document relation not found")
