import os
import io
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.config.s3 import get_client
from typing import Annotated, List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, UTC
import uuid
from api.config.config import get_settings, Settings
from botocore.exceptions import ClientError

router = APIRouter()

TEMP_FOLDER = os.path.join("tmp")
DATETIME_FORMAT = "%Y-%m-%d %H:%M%S:Z"


class ImageRaw(BaseModel):
    username: str
    content: bytes


class ImageInfo(BaseModel):
    image_id: str
    image_name: str
    bucket_path: str
    created_at: str


class ImageResponse(ImageInfo):
    created_by: str


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
    file: bytes, bucket: str, tmp_folder: str
) -> tuple[str, ImageInfo]:
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


# @router.get("/api/internal/mongodb/entity/user/{user_id}", response_model=UserResponse)
# async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
#     if current_user["user_id"] != user_id and "superadmin" not in current_user.get(
#         "roles", []
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     async with get_db_client() as db:
#         user = await db.users.find_one({"_id": ObjectId(user_id)})
#         if user:
#             user["user_id"] = str(user["_id"])
#             return UserResponse(**user)
#         raise HTTPException(status_code=404, detail="User not found")


# @router.put("/api/internal/mongodb/entity/user/{user_id}", response_model=UserResponse)
# async def update_user(
#     user_id: str, user: User, current_user: dict = Depends(get_current_user)
# ):
#     if current_user["user_id"] != user_id and "superadmin" not in current_user.get(
#         "roles", []
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     async with get_db_client() as db:
#         user_dict = user.model_dump()
#         user_dict["password"] = hash_password(
#             user_dict["password"]
#         )  # Hash the password before storing
#         result = await db.users.update_one(
#             {"_id": ObjectId(user_id)}, {"$set": user_dict}
#         )
#         if result.modified_count == 1:
#             user = await db.users.find_one({"_id": ObjectId(user_id)})
#             user["user_id"] = str(user["_id"])
#             return UserResponse(**user)
#         raise HTTPException(status_code=404, detail="User not found")


# @router.delete("/api/internal/mongodb/entity/user/{user_id}", response_model=dict)
# async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
#     if current_user["user_id"] != user_id and "superadmin" not in current_user.get(
#         "roles", []
#     ):
#         raise HTTPException(status_code=403, detail="Not enough permissions")

#     async with get_db_client() as db:
#         result = await db.users.delete_one({"_id": ObjectId(user_id)})
#         if result.deleted_count == 1:
#             # Invalidate the user's JWT token
#             # This can be done by removing the token from a blacklist or setting an expiration date
#             # For simplicity, we'll assume tokens are short-lived and do not implement a blacklist here
#             return {"message": "User deleted successfully"}
#         raise HTTPException(status_code=404, detail="User not found")
