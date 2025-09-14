import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Variables pour l'API MongoDB
    API_MONGODB_BASE_URL: str = os.getenv("API_MONGODB_BASE_URL", "")
    API_MONGODB_API_GATEWAY_CA_PATH: str = os.getenv("API_MONGODB_API_GATEWAY_CA_PATH", "")
    API_MONGODB_API_GATEWAY_KEY_PATH: str = os.getenv("API_MONGODB_API_GATEWAY_KEY_PATH", "")
    API_MONGODB_API_GATEWAY_CERT_PATH: str = os.getenv("API_MONGODB_API_GATEWAY_CERT_PATH", "")
    # Variables pour l'API PostgreSQL
    API_POSTGRESQL_BASE_URL: str = os.getenv("API_POSTGRESQL_BASE_URL", "")
    API_POSTGRESQL_API_GATEWAY_CA_PATH: str = os.getenv("API_POSTGRESQL_API_GATEWAY_CA_PATH", "")
    API_POSTGRESQL_API_GATEWAY_KEY_PATH: str = os.getenv("API_POSTGRESQL_API_GATEWAY_KEY_PATH", "")
    API_POSTGRESQL_API_GATEWAY_CERT_PATH: str = os.getenv("API_POSTGRESQL_API_GATEWAY_CERT_PATH", "")
    API_GATEWAY_PROTECTED_ENDPOINT_URL: str = os.getenv("API_GATEWAY_PROTECTED_ENDPOINT_URL", "")
    PROTECTED_ENDPOINT_URL: str = os.getenv("API_GATEWAY_PROTECTED_ENDPOINT_URL", "")
    HOST: str = os.getenv("API_GATEWAY_HOST", "")
    # Variables pour l'authentification
    INTERNAL_SECRET_KEY: str = os.getenv("API_GATEWAY_INTERNAL_SECRET_KEY", "")
    ALGORITHM: str = os.getenv("API_GATEWAY_ALGORITHM", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("API_GATEWAY_ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Valeur par défaut de 30 minutes

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set INTERNAL_SECRET_KEY by reading from the file specified by API_GATEWAY_INTERNAL_SECRET_KEY_PATH
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


settings = Settings()
