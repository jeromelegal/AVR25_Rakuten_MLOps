from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from config.db import get_db_client
from datetime import datetime, timezone
from config.settings import Settings
from api.auth import get_current_user
from typing import Dict

router = APIRouter()

class Image(BaseModel):
    image_name: str
    bucket_name: str

class ImageResponse(BaseModel):
    id: int
    image_name: str
    bucket_name: str
    created_at: datetime
    created_by: int

@router.post("/api/internal/postgresql/entity/image", response_model=ImageResponse)
async def create_image(request: Request, data: Image, current_user: Dict = Depends(get_current_user)):
    settings: Settings = request.app.state.settings

    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")


    data_dict = data.model_dump()
    data_dict["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    data_dict["created_by"] = current_user["id"]

    async with get_db_client(settings) as conn:
        image_id = await conn.fetchval(
            "INSERT INTO images (image_name, bucket_name, created_at, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            data_dict["image_name"],
            data_dict["bucket_name"],
            data_dict["created_at"],
            data_dict["created_by"]
        )
        data_dict["id"] = str(image_id)
        return ImageResponse(**data_dict)

@router.get("/api/internal/postgresql/entity/image/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, current_user: Dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    
    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        image = await conn.fetchrow(
            "SELECT id, image_name, bucket_name, created_at, created_by FROM images WHERE id = $1",
            image_id
        )
        if image:
            return ImageResponse(**image)
        raise HTTPException(status_code=404, detail="Image not found")

@router.put("/api/internal/postgresql/entity/image/{image_id}", response_model=ImageResponse)
async def update_image(image_id: int, data: Image, current_user: Dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings

    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    data_dict = data.model_dump()
    async with get_db_client(settings) as conn:
        await conn.execute(
            "UPDATE images SET image_name = $1, bucket_name = $2 WHERE id = $3",
            data_dict["image_name"],
            data_dict["bucket_name"],
            image_id
        )
        updated_image = await conn.fetchrow(
            "SELECT id, image_name, bucket_name, created_at, created_by "
            "FROM images WHERE id = $1",
            image_id
        )
        if updated_image:
            if updated_image["image_name"] == data_dict["image_name"]:
                if updated_image["bucket_name"] == data_dict["bucket_name"]:
                    return ImageResponse(**updated_image)
                raise HTTPException(status_code=500, detail="Error during update 'bucket_name'")
            raise HTTPException(status_code=500, detail="Error during update 'image_name'")
        raise HTTPException(status_code=404, detail="Image not found to update")

@router.delete("/api/internal/postgresql/entity/image/{image_id}", response_model=Dict)
async def delete_image(image_id: int, current_user: Dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    
    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM images WHERE id = $1",
            image_id
        )
        if result == "DELETE 1":
            return {"message": "Image deleted successfully"}
        raise HTTPException(status_code=404, detail="Image not found")



