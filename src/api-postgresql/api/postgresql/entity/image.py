from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, UUID4
from config.db import get_db_client
from datetime import datetime
from config.settings import Settings
from api.auth import get_current_user
from typing import Dict, Optional

router = APIRouter()

class Image(BaseModel):
    image_name: str
    image_uuid: str
    bucket_path: str
    created_at: Optional[datetime] = None
    created_by: int

class ImageResponse(BaseModel):
    id: int
    image_name: str
    image_uuid: str
    bucket_path: str
    created_at: datetime
    created_by: int

@router.post("/api/internal/postgresql/entity/image", response_model=ImageResponse)
async def create_image(request: Request, data: Image, current_user: Dict = Depends(get_current_user)):
    settings: Settings = request.app.state.settings

    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")


    data_dict = data.model_dump()
    # data_dict["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    # data_dict["created_by"] = current_user["id"]
    async with get_db_client(settings) as conn:
        image_id = await conn.fetchval(
            "INSERT INTO images (image_name, image_uuid, bucket_path, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            data_dict["image_name"],
            data_dict["image_uuid"],
            data_dict["bucket_path"],
            data_dict["created_by"],
        )
        row = await conn.fetchrow(
            "SELECT id, image_name, image_uuid, bucket_path, created_at, created_by FROM images WHERE id = $1",
            image_id
        )
        return ImageResponse(**row)

@router.get("/api/internal/postgresql/entity/image/{image_id}", response_model=ImageResponse)
async def get_image(image_id: int, current_user: Dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    
    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        image = await conn.fetchrow(
            "SELECT id, image_name, image_uuid, bucket_path, created_at, created_by FROM images WHERE id = $1",
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
            "UPDATE images SET image_name = $1, image_uuid = $2, bucket_path = $3 WHERE id = $4",
            data_dict["image_name"],
            data_dict["image_uuid"],
            data_dict["bucket_path"],
            image_id
        )
        updated_image = await conn.fetchrow(
            "SELECT id, image_name, image_uuid, bucket_path, created_at, created_by "
            "FROM images WHERE id = $1",
            image_id
        )
        if updated_image:
            if updated_image["image_name"] == data_dict["image_name"]:
                if updated_image["image_uuid"] == data_dict["image_uuid"]:
                    if updated_image["bucket_path"] == data_dict["bucket_path"]:
                        return ImageResponse(**updated_image)
                    raise HTTPException(status_code=500, detail="Error during update 'bucket_path'")
                raise HTTPException(status_code=500, detail="Error during update 'image_uuid'")
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



