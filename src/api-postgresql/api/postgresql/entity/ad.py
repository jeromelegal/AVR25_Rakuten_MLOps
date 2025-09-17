from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from config.db import get_db_client
from typing import Optional
from datetime import datetime, timezone
from config.settings import Settings
from api.auth import get_current_user
from typing import Dict

router = APIRouter()

class Ad(BaseModel):
    designation: str
    description: Optional[str]

class AdResponse(BaseModel):
    id: int
    designation: str
    description: Optional[str]
    created_at: datetime
    created_by: int

@router.post("/api/internal/postgresql/entity/ad", response_model=AdResponse)
async def create_ad(request: Request, data: Ad, current_user: dict = Depends(get_current_user)):
    settings: Settings = request.app.state.settings

    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")


    data_dict = data.model_dump()
    data_dict["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    data_dict["created_by"] = current_user["id"]

    async with get_db_client(settings) as conn:
        ad_id = await conn.fetchval(
            "INSERT INTO ads (designation, description, created_at, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            data_dict["designation"],
            data_dict["description"],
            data_dict["created_at"],
            data_dict["created_by"]
        )
        data_dict["id"] = str(ad_id)
        return AdResponse(**data_dict)

@router.get("/api/internal/postgresql/entity/ad/{ad_id}", response_model=AdResponse)
async def get_ad(ad_id: int, current_user: Dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    
    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        ad = await conn.fetchrow(
            "SELECT id as ad_id, designation, description, created_at, created_by FROM ads WHERE id = $1",
            ad_id
        )
        if ad:
            return AdResponse(**ad)
        raise HTTPException(status_code=404, detail="Ad not found")

@router.put("/api/internal/postgresql/entity/ad/{ad_id}", response_model=Dict)
async def update_ad(ad_id: int, data: Ad, current_user: Dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    
    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    data_dict = data.model_dump()
    async with get_db_client(settings) as conn:
        await conn.execute(
            "UPDATE ads SET designation = $1, description = $2 WHERE id = $3",
            data_dict["designation"],
            data_dict["description"],
            ad_id
        )
        updated_ad = await conn.fetchrow(
            "SELECT id as ad_id, designation, description, created_at, created_by "
            "FROM ads WHERE id = $1",
            ad_id
        )
        if updated_ad:
            if updated_ad["designation"] == data_dict["designation"]:
                if updated_ad["description"] == data_dict["description"]:
                    return {"message": "Ad updated successfully"}
                raise HTTPException(status_code=500, detail="Error during update 'description'")
            raise HTTPException(status_code=500, detail="Error during update 'designation'")
        raise HTTPException(status_code=404, detail="Ad not found to update")

@router.delete("/api/internal/postgresql/entity/ad/{ad_id}", response_model=Dict)
async def delete_ad(ad_id: int, current_user: Dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings

    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM ads WHERE id = $1",
            ad_id
        )
        if result == "DELETE 1":
            return {"message": "Ad deleted successfully"}
        raise HTTPException(status_code=404, detail="Ad not found")



