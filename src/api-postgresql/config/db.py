import os
from contextlib import asynccontextmanager
from config.config import POSTGRESQL_USER, POSTGRESQL_PASSWORD, POSTGRESQL_SERVICE_NAME, POSTGRESQL_SERVICE_PORT, POSTGRESQL_DATABASE, POSTGRESQL_API_POSTGRESQL_CA_PATH, POSTGRESQL_API_POSTGRESQL_CERT_PATH, POSTGRESQL_API_POSTGRESQL_KEY_PATH
import asyncpg
import ssl

async def get_db():
    # Configuration de la connexion SSL
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=POSTGRESQL_API_POSTGRESQL_CA_PATH)
    ssl_context.load_cert_chain(certfile=POSTGRESQL_API_POSTGRESQL_CERT_PATH, keyfile=POSTGRESQL_API_POSTGRESQL_KEY_PATH)

    # Connexion à la base de données PostgreSQL
    conn = await asyncpg.connect(
        user=POSTGRESQL_USER,
        password=POSTGRESQL_PASSWORD,
        database=POSTGRESQL_DATABASE,
        host=POSTGRESQL_SERVICE_NAME,
        port=POSTGRESQL_SERVICE_PORT,
        ssl=ssl_context
    )
    return conn

@asynccontextmanager
async def get_db_client():
    # Configuration de la connexion SSL
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=POSTGRESQL_API_POSTGRESQL_CA_PATH)
    ssl_context.load_cert_chain(certfile=POSTGRESQL_API_POSTGRESQL_CERT_PATH, keyfile=POSTGRESQL_API_POSTGRESQL_KEY_PATH)

    # Connexion à la base de données PostgreSQL
    conn = await asyncpg.connect(
        user=POSTGRESQL_USER,
        password=POSTGRESQL_PASSWORD,
        database=POSTGRESQL_DATABASE,
        host=POSTGRESQL_SERVICE_NAME,
        port=POSTGRESQL_SERVICE_PORT,
        ssl=ssl_context
    )
    try:
        yield conn
    finally:
        await conn.close()
