from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC
from enum import Enum
from pymongo import ReturnDocument

router = APIRouter()

class Category(Enum):
    LIVRE_OCCASION = (10, "Livre occasion")
    JEU_VIDEO_ACCESSOIRE_TECH = (40, "Jeu vidéo, accessoire tech.")
    ACCESSOIRE_CONSOLE = (50, "Accessoire Console")
    CONSOLE_DE_JEU = (60, "Console de jeu")
    FIGURINE = (1140, "Figurine")
    CARTE_COLLECTION = (1160, "Carte Collection")
    JEU_PLATEAU = (1180, "Jeu Plateau")
    JOUET_ENFANT_DEGUISEMENT = (1280, "Jouet enfant, déguisement")
    JEU_DE_SOCIETE = (1281, "Jeu de société")
    JOUET_TECH = (1300, "Jouet tech")
    PAIRE_DE_CHAUSSETTES = (1301, "Paire de chaussettes")
    JEU_EXTERIEUR_VETEMENT = (1302, "Jeu extérieur, vêtement")
    AUTOUR_DU_BEBE = (1320, "Autour du bébé")
    MOBILIER_INTERIEUR = (1560, "Mobilier intérieur")
    CHAMBRE = (1920, "Chambre")
    CUISINE = (1940, "Cuisine")
    DECORATION_INTERIEURE = (2060, "Décoration intérieure")
    ANIMAL = (2220, "Animal")
    REVUES_ET_JOURNAUX = (2280, "Revues et journaux")
    MAGAZINES_LIVRES_ET_BDS = (2403, "Magazines, livres et BDs")
    JEU_OCCASION = (2462, "Jeu occasion")
    BUREAUTIQUE_ET_PAPETERIE = (2522, "Bureautique et papeterie")
    MOBILIER_EXTERIEUR = (2582, "Mobilier extérieur")
    AUTOUR_DE_LA_PISCINE = (2583, "Autour de la piscine")
    BRICOLAGE = (2585, "Bricolage")
    LIVRE_NEUF = (2705, "Livre neuf")
    JEU_PC = (2905, "Jeu PC")

    def __new__(cls, code: int, label: str):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.label = label
        return obj

    def __str__(self) -> str:
        return self.label

    @classmethod
    def from_label(cls, label: str) -> "Category":
        for m in cls:
            if m.label == label:
                return m
        raise ValueError(f"Libellé inconnu: {label!r}")

class Ad(BaseModel):
    designation: str
    description: str
    image_name: str
    bucket_name: str = Field(default="default-bucket")
    category: Category

    # INPUT: accept label ("Jeu PC"), code (2905) or enum name ("JEU_PC")
    @field_validator("category", mode="before")
    @classmethod
    def parse_category(cls, v):
        if isinstance(v, Category):
            return v
        if isinstance(v, int):
            return Category(v)
        if isinstance(v, str):
            try:
                return Category[v]
            except KeyError:
                return Category.from_label(v)
        raise TypeError("Invalid category (require: code int, enum name or label)")

class CategoryOut(BaseModel):
    code: int
    label: str
class AdResponse(BaseModel):
    ad_id: str
    designation: str
    description: str
    image_name: str
    bucket_name: str
    category: CategoryOut
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/ad", response_model=AdResponse)
async def create_ad(ad: Ad, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        now = datetime.now(UTC).isoformat()
        category_code = ad.category.value
        category_label = ad.category.label
        ad_dict = ad.model_dump(exclude={"category"})
        ad_dict["created_at"] = now  # Set the creation date
        ad_dict["created_by"] = current_user["user_id"]  # Set the creator
        # Insert ad in bdd 'ads'
        res = await db.ads.insert_one(ad_dict)
        ad_id = res.inserted_id
        # Insert category in bdd 'categories'
        cat_doc = await db.categories.find_one_and_update(
            {"code": category_code},
            {"$setOnInsert": {"code": category_code, "label": category_label, "created_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        category_id = cat_doc["_id"]
        # Insert relation in bdd 'ad_category'
        await db.ad_categories.update_one(
            {"ad_id": ad_id},
            {"$set": {"ad_id": ad_id, "category_id": category_id, "created_at": now}},
            upsert=True,
        )
        return AdResponse(
            ad_id=str(ad_id),
            designation=ad_dict["designation"],
            description=ad_dict["description"],
            image_name=ad_dict["image_name"],
            bucket_name=ad_dict["bucket_name"],
            category=CategoryOut(code=cat_doc["code"], label=cat_doc["label"]),
            created_at=ad_dict["created_at"],
            created_by=ad_dict["created_by"],
        )

@router.get("/api/internal/mongodb/entity/ad/{ad_id}", response_model=AdResponse)
async def get_ad(ad_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        ad = await db.ads.find_one({"_id": ObjectId(ad_id)})
        if not ad:
            raise HTTPException(status_code=404, detail="Ad not found")
        link = await db.ad_categories.find_one({"ad_id": ad["_id"]})
        if not link:
            raise HTTPException(status_code=404, detail="Ad category relation not found")
        cat = await db.categories.find_one({"_id": link["category_id"]})
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        return AdResponse(
            ad_id=str(ad["_id"]),
            designation=ad["designation"],
            description=ad["description"],
            image_name=ad["image_name"],
            bucket_name=ad["bucket_name"],
            category=CategoryOut(code=cat["code"], label=cat["label"]),
            created_at=ad["created_at"],
            created_by=ad["created_by"],
        )

@router.put("/api/internal/mongodb/entity/ad/{ad_id}", response_model=AdResponse)
async def update_ad(ad_id: str, ad: Ad, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        # Update ad without category
        ad_dict = ad.model_dump(exclude={"category"})
        result = await db.ads.update_one({"_id": ObjectId(ad_id)}, {"$set": ad_dict})
        if result.matched_count != 1:
            raise HTTPException(status_code=404, detail="Ad not found")
        # Update category
        code = ad.category.value
        label = ad.category.label
        cat_doc = await db.categories.find_one_and_update(
            {"code": code},
            {"$setOnInsert": {"code": code, "label": label}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        # Update relation
        await db.ad_categories.update_one(
            {"ad_id": ObjectId(ad_id)},
            {"$set": {"category_id": cat_doc["_id"]}},
            upsert=True,
        )
        # Read ad to response
        ad_db = await db.ads.find_one({"_id": ObjectId(ad_id)})
        return AdResponse(
            ad_id=str(ad_db["_id"]),
            designation=ad_db["designation"],
            description=ad_db["description"],
            image_name=ad_db["image_name"],
            bucket_name=ad_db["bucket_name"],
            category=CategoryOut(code=cat_doc["code"], label=cat_doc["label"]),
            created_at=ad_db["created_at"],
            created_by=ad_db["created_by"],
        )

@router.delete("/api/internal/mongodb/entity/ad/{ad_id}", response_model=dict)
async def delete_ad(ad_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.ads.delete_one({"_id": ObjectId(ad_id)})
        if result.deleted_count != 1:
            raise HTTPException(status_code=404, detail="Ad not found")
        await db.ad_categories.delete_many({"ad_id": ObjectId(ad_id)})
        return {"message": "Ad deleted successfully"}
