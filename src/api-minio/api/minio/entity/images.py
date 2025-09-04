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

CONTENT_RESPONSE_KEY = "Contents"


class ImageRaw(BaseModel):
    username: str
    content: bytes


class ImageInfo(BaseModel):
    image_id: str
    image_name: str
    bucket_path: str
    created_at: str


class ImageUpdateRaw(ImageRaw):
    image_id: str


class ImageResponse(ImageInfo):
    created_by: str


class ImageContent(BaseModel):
    image_id: str
    content: bytes


class ImageNames(BaseModel):
    names: List[str]


class ImageDeleted(BaseModel):
    deleted_image: str


@router.post("/api/internal/minio/entity/image", response_model=ImageResponse)
async def store_image(
    image: ImageRaw,
    settings: Annotated[Settings, Depends(get_settings)],
    tmp_folder: str = TEMP_FOLDER,
):
    client = get_client(settings=settings)
    tmp_path, info = _store_temp_image_from_bytes(
        file=image.content, bucket=settings.MINIO_BUCKET_NAME, tmp_folder=tmp_folder
    )

    exception = None

    try:
        client.upload_file(tmp_path, settings.MINIO_BUCKET_NAME, info.image_id)
    except ClientError as e:
        exception = HTTPException(
            status_code=500,
            detail=f"Impossible to store image {info.image_name}: {e}",
        )
    finally:
        _delete_temp_file(tmp_path=tmp_path)

    if exception is not None:
        raise exception

    return ImageResponse(
        image_id=info.image_id,
        image_name=info.image_name,
        bucket_path=info.bucket_path,
        created_at=info.created_at,
        created_by=image.username,
    )


def _store_temp_image_from_bytes(
    file: bytes, bucket: str, tmp_folder: str, image_id: str = None
) -> tuple[str, ImageInfo]:
    if image_id is None:
        image_id = uuid.uuid4()
    # TODO: Accept other format on top of JPG
    image_path = os.path.join(bucket, f"{image_id}.jpg")

    stream = io.BytesIO(file)
    image = Image.open(stream)
    image_id = str(uuid.uuid4())
    info = ImageInfo(
        image_id=image_id,
        image_name=image.filename,
        bucket_path=image_path,
        created_at=datetime.now().strftime(format=DATETIME_FORMAT),
    )

    tmp_path = os.path.join(tmp_folder, f"{image_id}.jpg")
    image.save(tmp_path)

    return tmp_path, info


def _delete_temp_file(tmp_path: str):
    if os.path.exists(path=tmp_path):
        os.remove(path=tmp_path)


@router.get(
    "/api/internal/minio/entity/images",
    response_model=ImageNames,
)
async def list_files(
    settings: Annotated[Settings, Depends(get_settings)],
    limit: int = 1000,
    start_after: str = "",
) -> ImageNames:
    try:
        client = get_client(settings=settings)
        response = client.list_objects_v2(
            Bucket=settings.MINIO_BUCKET_NAME, MaxKeys=limit, StartAfter=start_after
        )

    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Impossible to get the buckets from the Minio server: {e}",
        )
    if CONTENT_RESPONSE_KEY not in response:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process get files from Minio server: {response}",
        )
    return ImageNames(names=[el["Key"] for el in response[CONTENT_RESPONSE_KEY]])


@router.get(
    "/api/internal/minio/entity/image/{image_id}",
    response_model=ImageContent,
)
async def get_image(
    image_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    tmp_folder: str = TEMP_FOLDER,
):
    exception = None
    try:
        tmp_image_path = os.path.join(tmp_folder, f"{image_id}.jpg")
        client = get_client(settings=settings)
        client.download_file(
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=image_id,
            Filename=tmp_image_path,
        )
        with open(tmp_image_path, "rb") as f:
            content = f.read()

    except ClientError as e:
        exception = HTTPException(
            status_code=500,
            detail=f"Impossible to download the file {image_id} from the Minio server: {e}",
        )
    finally:
        _delete_temp_file(tmp_path=tmp_image_path)

    if exception is not None:
        raise exception

    return ImageContent(image_id=image_id, content=content)


@router.put("/api/internal/minio/entity/image/{image_id}", response_model=ImageResponse)
async def update_image(
    update: ImageUpdateRaw,
    settings: Annotated[Settings, Depends(get_settings)],
    tmp_folder: str = TEMP_FOLDER,
):
    client = get_client(settings=settings)
    tmp_path, info = _store_temp_image_from_bytes(
        file=update.content,
        bucket=settings.MINIO_BUCKET_NAME,
        tmp_folder=tmp_folder,
        image_id=update.image_id,
    )

    exception = None

    try:
        client.upload_file(tmp_path, settings.MINIO_BUCKET_NAME, info.image_id)
    except ClientError as e:
        exception = HTTPException(
            status_code=500,
            detail=f"Impossible to store image {info.image_name}: {e}",
        )
    finally:
        _delete_temp_file(tmp_path=tmp_path)

    if exception is not None:
        raise exception

    return ImageResponse(
        image_id=info.image_id,
        image_name=info.image_name,
        bucket_path=info.bucket_path,
        created_at=info.created_at,
        created_by=update.username,
    )


@router.delete(
    "/api/internal/minio/entity/image/{image_id}", response_model=ImageDeleted
)
async def delete_image(
    image_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        client = get_client(settings=settings)
        response = client.delete_object(Bucket=settings.MINIO_BUCKET_NAME, Key=image_id)

    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Impossible to delete the image {image_id} from the Minio server: {e}",
        )
    return ImageDeleted(deleted_image=image_id)
