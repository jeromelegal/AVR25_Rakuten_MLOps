import os
from contextlib import asynccontextmanager
# from config.config import settings.POSTGRESQL_USER, settings.POSTGRESQL_PASSWORD, settings.POSTGRESQL_SERVICE_NAME, settings.POSTGRESQL_SERVICE_PORT, settings.POSTGRESQL_DATABASE, settings.POSTGRESQL_API_POSTGRESQL_CA_PATH, settings.POSTGRESQL_API_POSTGRESQL_CERT_PATH, settings.POSTGRESQL_API_POSTGRESQL_KEY_PATH
from config.settings import settings 

import asyncpg
import ssl

async def get_db():
    # Configuration de la connexion SSL
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=settings.POSTGRESQL_API_POSTGRESQL_CA_PATH)
    ssl_context.load_cert_chain(certfile=settings.POSTGRESQL_API_POSTGRESQL_CERT_PATH, keyfile=settings.POSTGRESQL_API_POSTGRESQL_KEY_PATH)

    # Connexion à la base de données PostgreSQL
    conn = await asyncpg.connect(
        user=settings.POSTGRESQL_USER,
        password=settings.POSTGRESQL_PASSWORD,
        database=settings.POSTGRESQL_DATABASE,
        host=settings.POSTGRESQL_SERVICE_NAME,
        port=settings.POSTGRESQL_SERVICE_PORT,
        ssl=ssl_context
    )
    return conn

@asynccontextmanager
async def get_db_client():
    # Configuration de la connexion SSL
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=settings.POSTGRESQL_API_POSTGRESQL_CA_PATH)
    ssl_context.load_cert_chain(certfile=settings.POSTGRESQL_API_POSTGRESQL_CERT_PATH, keyfile=settings.POSTGRESQL_API_POSTGRESQL_KEY_PATH)

    # Connexion à la base de données PostgreSQL
    conn = await asyncpg.connect(
        user=settings.POSTGRESQL_USER,
        password=settings.POSTGRESQL_PASSWORD,
        database=settings.POSTGRESQL_DATABASE,
        host=settings.POSTGRESQL_SERVICE_NAME,
        port=settings.POSTGRESQL_SERVICE_PORT,
        ssl=ssl_context
    )
    try:
        yield conn
    finally:
        await conn.close()
