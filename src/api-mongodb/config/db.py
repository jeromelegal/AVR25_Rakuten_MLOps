from motor.motor_asyncio import AsyncIOMotorClient
import os
from contextlib import asynccontextmanager
# from config.config import MONGODB_USER, MONGODB_PASSWORD, MONGODB_SERVICE_NAME, MONGODB_SERVICE_PORT, MONGODB_DATABASE, MONGODB_API_MONGODB_CA_PATH, MONGODB_API_MONGODB_PEM_PATH
from config.settings import settings 

from urllib.parse import quote_plus


async def get_db():
    escaped_username = quote_plus(settings.MONGODB_USER)
    escaped_password = quote_plus(settings.MONGODB_PASSWORD)
    mongodb_uri = f"mongodb://{escaped_username}:{escaped_password}@{settings.MONGODB_SERVICE_NAME}:{settings.MONGODB_SERVICE_PORT}/{settings.MONGODB_DATABASE}?authSource={settings.MONGODB_DATABASE}"

    print(f"Connecting to MongoDB with URI: {mongodb_uri}")  # Affiche l'URI pour vérification

    client = AsyncIOMotorClient(
        mongodb_uri,
        tls=True,
        tlsCAFile=settings.MONGODB_API_MONGODB_CA_PATH,
        tlsCertificateKeyFile=settings.MONGODB_API_MONGODB_PEM_PATH,
        tlsAllowInvalidCertificates=False  # Assurez-vous que les certificats sont valides
    )
    db = client.file_storage
    return db

@asynccontextmanager
async def get_db_client():
    escaped_username = quote_plus(settings.MONGODB_USER)
    escaped_password = quote_plus(settings.MONGODB_PASSWORD)
    mongodb_uri = f"mongodb://{escaped_username}:{escaped_password}@{settings.MONGODB_SERVICE_NAME}:{settings.MONGODB_SERVICE_PORT}/{settings.MONGODB_DATABASE}"

    client = AsyncIOMotorClient(
        mongodb_uri,
        tls=True,
        tlsCAFile=settings.MONGODB_API_MONGODB_CA_PATH,
        tlsCertificateKeyFile=settings.MONGODB_API_MONGODB_PEM_PATH,
        tlsAllowInvalidCertificates=False  # Assurez-vous que les certificats sont valides
    )
    try:
        yield client.file_storage
    finally:
        client.close()
