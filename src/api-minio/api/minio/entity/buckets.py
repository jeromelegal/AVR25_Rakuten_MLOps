import os
import io
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.config.s3 import get_client
from typing import Annotated, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, UTC
import uuid
from api.config.config import get_settings, Settings
from botocore.exceptions import ClientError

router = APIRouter()

TEMP_FOLDER = os.path.join("tmp")
DATETIME_FORMAT = "%Y-%m-%d %H:%M%S:Z"

BUCKET_RESPONSE_KEY = "Buckets"


class Bucket(BaseModel):
    name: str
    creation_date: datetime


class DeletedBucket(BaseModel):
    name: str
    deletion_date: datetime


class Buckets(BaseModel):
    buckets: List[Bucket]


@router.post("/api/internal/minio/entity/bucket", response_model=Bucket)
async def create_bucket(
    bucket_name: str,
    settings: Annotated[Settings, Depends(get_settings)],
):
    client = get_client(settings=settings)

    try:
        client.create_bucket(
            ACL="private",
            Bucket=bucket_name,
            CreateBucketConfiguration={
                "LocationConstraint": "eu-central-1",
            },
        )
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Impossible to create the bucket {bucket_name}: {e}",
        )

    return Bucket(name=bucket_name, creation_date=datetime.now())


@router.delete("/api/internal/minio/entity/bucket", response_model=DeletedBucket)
async def delete_bucket(
    bucket_name: str,
    settings: Annotated[Settings, Depends(get_settings)],
):
    client = get_client(settings=settings)

    try:
        client.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Impossible to delete the bucket {bucket_name}: {e}",
        )

    return DeletedBucket(name=bucket_name, deletion_date=datetime.now())


@router.get(
    "/api/internal/minio/entity/buckets",
    response_model=Buckets,
)
async def get_buckets(
    settings: Annotated[Settings, Depends(get_settings)],
    limit: int = 1000,
) -> Buckets:
    client = get_client(settings=settings)
    try:
        response = client.list_buckets(MaxBuckets=limit)
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Impossible to get the buckets from the Minio server: {e}",
        )
    if BUCKET_RESPONSE_KEY not in response:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process reponse from Minio server: {response}",
        )
    return Buckets(
        buckets=[
            Bucket(name=el["Name"], creation_date=el["CreationDate"])
            for el in response[BUCKET_RESPONSE_KEY]
        ]
    )
