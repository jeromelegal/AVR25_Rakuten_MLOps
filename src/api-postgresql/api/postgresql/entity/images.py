from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from config.db import get_db_client
from typing import Optional
from datetime import datetime, timezone, timedelta, UTC
from config.settings import Settings
from api.auth import get_current_user, hash_password, create_access_token
import asyncpg
from typing import Dict

router = APIRouter()

class Image(BaseModel):
    imagename: str
    bucketname: str

class ImageResponse(BaseModel):
    id: int
    imagename: str
    bucketname: str
    created_at: datetime
    created_by: int

@router.post("/api/internal/postgresql/entity/image", response_model=ImageResponse)
async def create_image(request: Request, data: Image):
    settings: Settings = request.app.state.settings
    data_dict = data.model_dump()
    data_dict["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    data_dict["created_by"] = 0  # Assuming the system creates the user

    async with get_db_client(settings) as conn:
        image_id = await conn.fetchval(
            "INSERT INTO ads (designation, bucketname, created_at, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            data_dict["imagename"],
            data_dict["bucketname"],
            data_dict["created_at"],
            data_dict["created_by"]
        )
        data_dict["id"] = str(image_id)
        return ImageResponse(**data_dict)

@router.get("/api/internal/postgresql/entity/image/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        image = await conn.fetchrow(
            "SELECT id as image_id, imagename, bucketname, created_at, created_by FROM images WHERE id = $1",
            int(image_id)
        )
        if image:
            return ImageResponse(**image)
        raise HTTPException(status_code=404, detail="Image not found")

@router.put("/api/internal/postgresql/entity/image/{image_id}", response_model=dict)
async def update_image(image_id: int, data: Image, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # print("\n"*20)
    # print(f"{current_user["id"]} != {user_id}")
    # print("\n"*20)
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    data_dict = data.model_dump()
    async with get_db_client(settings) as conn:
        await conn.execute(
            "UPDATE images SET imagename = $1, bucketname = $2 WHERE id = $3",
            data_dict["imagename"],
            data_dict["bucketname"],
            image_id
        )
        updated_ad = await conn.fetchrow(
            "SELECT id as image_id, imagename, bucketname, created_at, created_by "
            "FROM images WHERE id = $1",
            image_id
        )
        if updated_ad:
            if updated_ad["imagename"] == data_dict["imagename"]:
                if updated_ad["bucketname"] == data_dict["bucketname"]:
                    return {"message": "Image updated successfully"}
                raise HTTPException(status_code=500, detail="Error during update 'bucketname'")
            raise HTTPException(status_code=500, detail="Error during update 'imagename'")
        raise HTTPException(status_code=404, detail="Image not found to update")

@router.delete("/api/internal/postgresql/entity/image/{image_id}", response_model=dict)
async def delete_image(image_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # print("\n"*20)
    # print(f"{current_user["id"]} != {user_id}")
    # print("\n"*20)
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM images WHERE id = $1",
            int(image_id)
        )
        if result == "DELETE 1":
            return {"message": "Image deleted successfully"}
        raise HTTPException(status_code=404, detail="Image not found")



