from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from config.db import get_db_client
from config.settings import Settings
from api.auth import get_current_user


router = APIRouter()

class ImageAdRelation(BaseModel):
    image_id: int
    ad_id: int

class ImageAdResponse(BaseModel):
    image_id: int
    ad_id: int

@router.get("/api/internal/postgresql/relation/images_ads/{image_id}", response_model=ImageAdResponse)
async def get_ad_image(image_id: int=None, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    
    async with get_db_client(settings) as conn:
        if image_id is not None:
            relation = await conn.fetchrow(
                "SELECT ad_id, image_id FROM ads_images WHERE image_id = $1",
                image_id
            )
            if relation:
                return ImageAdResponse(**relation)
            else:
                raise HTTPException(status_code=404, detail="Image-Ad relation not found")
        else:
            raise HTTPException(status_code=400, detail="Missing image_id.")