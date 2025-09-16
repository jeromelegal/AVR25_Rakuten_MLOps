import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

router = APIRouter()

class UserSignup(BaseModel):
    username: str
    email: str
    password: str

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

def get_client_manager(request: Request) -> ClientManager:
    settings = get_settings(request)
    return create_client_manager(settings)

@router.post("/signup")
async def signup(
    request: Request,
    user: UserSignup,
    client_manager: ClientManager = Depends(get_client_manager)
):
    try:
        # Obtenez les clients directement
        mongodb_client = client_manager.get_client("mongodb")
        postgresql_client = client_manager.get_client("postgresql")

        user_data = {
            "username": user.username,
            "email": user.email,
            "password": user.password
        }

        logger.debug(f"Attempting to create user in MongoDB and PostgreSQL: {user.username}")

        # Créez l'utilisateur dans MongoDB
        mongodb_response = mongodb_client.create_entity(token=None, collection="user", entity_data=user_data)
        logger.debug(f"MongoDB response: {mongodb_response}")

        # Créez l'utilisateur dans PostgreSQL
        postgresql_response = postgresql_client.create_entity(token=None, table="user", entity_data=user_data)
        logger.debug(f"PostgreSQL response: {postgresql_response}")

        # Vérifiez si l'utilisateur a été créé avec succès dans les deux bases de données
        if mongodb_response and postgresql_response:
            logger.debug(f"User {user.username} created successfully in both databases")
            return {"message": "User created successfully"}
        else:
            logger.debug("Failed to create user in one of the databases. Rolling back...")

            # En cas d'échec dans l'une des bases de données, supprimez l'utilisateur de l'autre
            if mongodb_response:
                mongodb_uid = mongodb_response.get("user_id")
                mongodb_client.delete_entity(token=None, collection="user", entity_id=mongodb_uid)
                logger.debug("User deleted from MongoDB due to failure in PostgreSQL")

            if postgresql_response:
                postgresql_uid = postgresql_response.get("user_id")
                postgresql_client.delete_entity(token=None, table="user", entity_id=postgresql_uid)
                logger.debug("User deleted from PostgreSQL due to failure in MongoDB")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user in one of the databases"
            )
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup error: {str(e)}"
        )

@router.post("/signup/mongodb")
async def signup_mongodb(
    request: Request,
    user: UserSignup,
    client_manager: ClientManager = Depends(get_client_manager)
):
    try:
        mongodb_client = client_manager.get_client("mongodb")
        user_data = {
            "username": user.username,
            "email": user.email,
            "password": user.password
        }
        logger.debug(f"Attempting to create user in MongoDB: {user.username}")
        response = mongodb_client.create_entity(token=None, collection="user", entity_data=user_data)
        logger.debug(f"MongoDB create_user response: {response}")
        return {"message": "User created successfully in MongoDB", "user_id": response.get("user_id")}
    except Exception as e:
        logger.error(f"Signup error in MongoDB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup error in MongoDB: {str(e)}"
        )

@router.post("/signup/postgresql")
async def signup_postgresql(
    request: Request,
    user: UserSignup,
    client_manager: ClientManager = Depends(get_client_manager)
):
    try:
        postgresql_client = client_manager.get_client("postgresql")
        user_data = {
            "username": user.username,
            "email": user.email,
            "password": user.password
        }
        logger.debug(f"Attempting to create user in PostgreSQL: {user.username}")
        response = postgresql_client.create_entity(token=None, table="user", entity_data=user_data)
        logger.debug(f"PostgreSQL create_user response: {response}")
        return {"message": "User created successfully in PostgreSQL", "user_id": response.get("user_id")}
    except Exception as e:
        logger.error(f"Signup error in PostgreSQL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup error in PostgreSQL: {str(e)}"
        )
