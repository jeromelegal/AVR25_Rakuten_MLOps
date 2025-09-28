import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Configuration pour l'API Gateway
    API_GATEWAY_HOST: str = os.getenv("API_GATEWAY_HOST", "")
    INTERNAL_ENDPOINT_URL: str = os.getenv("API_GATEWAY_INTERNAL_ENDPOINT_URL", "/internal")
    PROTECTED_ENDPOINT_URL: str = os.getenv("API_GATEWAY_PROTECTED_ENDPOINT_URL", "/protected")

    # Configuration pour MongoDB
    API_MONGODB_BASE_URL: str = os.getenv("API_MONGODB_BASE_URL", "http://localhost:27017")
    MONGODB_SERVICE_PORT: str = os.getenv("MONGODB_SERVICE_PORT", "27017")
    MONGODB_SERVICE_NAME: str = os.getenv("MONGODB_SERVICE_NAME", "localhost")
    API_MONGODB_API_GATEWAY_CA_PATH: str = os.getenv("API_MONGODB_API_GATEWAY_CA_PATH", "")
    API_MONGODB_API_GATEWAY_KEY_PATH: str = os.getenv("API_MONGODB_API_GATEWAY_KEY_PATH", "")
    API_MONGODB_API_GATEWAY_CERT_PATH: str = os.getenv("API_MONGODB_API_GATEWAY_CERT_PATH", "")

    # Configuration pour PostgreSQL
    API_POSTGRESQL_BASE_URL: str = os.getenv("API_POSTGRESQL_BASE_URL", "http://localhost:5432")
    API_POSTGRESQL_API_GATEWAY_CA_PATH: str = os.getenv("API_POSTGRESQL_API_GATEWAY_CA_PATH", "")
    API_POSTGRESQL_API_GATEWAY_KEY_PATH: str = os.getenv("API_POSTGRESQL_API_GATEWAY_KEY_PATH", "")
    API_POSTGRESQL_API_GATEWAY_CERT_PATH: str = os.getenv("API_POSTGRESQL_API_GATEWAY_CERT_PATH", "")

    # Configuration pour Minio
    API_MINIO_BASE_URL: str = os.getenv("API_MINIO_BASE_URL", 'http://localhost:8020')
    API_MINIO_API_GATEWAY_CA_PATH: str = os.getenv("API_MINIO_API_GATEWAY_CA_PATH", "")
    API_MINIO_API_GATEWAY_KEY_PATH: str = os.getenv("API_MINIO_API_GATEWAY_KEY_PATH", "")
    API_MINIO_API_GATEWAY_CERT_PATH: str = os.getenv("API_MINIO_API_GATEWAY_CERT_PATH", "")

    # Configuration pour le traitement
    API_PROCESSING_BASE_URL: str = os.getenv("API_PROCESSING_BASE_URL", 'http://localhost:8050')
    API_PROCESSING_API_GATEWAY_CA_PATH: str = os.getenv("API_PROCESSING_API_GATEWAY_CA_PATH", "")
    API_PROCESSING_API_GATEWAY_KEY_PATH: str = os.getenv("API_PROCESSING_API_GATEWAY_KEY_PATH", "")
    API_PROCESSING_API_GATEWAY_CERT_PATH: str = os.getenv("API_PROCESSING_API_GATEWAY_CERT_PATH", "")

    # Configuration JWT
    SECRET_KEY: str = os.getenv("API_GATEWAY_SECRET_KEY", "test-secret-key")
    INTERNAL_SECRET_KEY: str = os.getenv("API_GATEWAY_INTERNAL_SECRET_KEY", "test-internal-secret-key")
    ALGORITHM: str = os.getenv("API_GATEWAY_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("API_GATEWAY_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        secret_key_path = os.getenv("API_GATEWAY_INTERNAL_SECRET_KEY_PATH")
        if secret_key_path:
            try:
                with open(secret_key_path, 'r') as file:
                    self.INTERNAL_SECRET_KEY = file.read().strip()
            except FileNotFoundError:
                self.INTERNAL_SECRET_KEY = ""
                print("Le fichier spécifié n'a pas été trouvé.")
            except Exception as e:
                self.INTERNAL_SECRET_KEY = ""
                print(f"Une erreur s'est produite : {e}")
        else:
            self.INTERNAL_SECRET_KEY = ""
            print("La variable d'environnement API_GATEWAY_INTERNAL_SECRET_KEY_PATH n'est pas définie.")

# Créez une instance de TestSettings pour l'utiliser dans vos tests
settings = Settings()
