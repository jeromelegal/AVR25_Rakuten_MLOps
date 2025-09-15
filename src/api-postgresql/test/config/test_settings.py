import os
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    API_GATEWAY_HOST: str = os.getenv("API_GATEWAY_HOST", "")
    INTERNAL_ENDPOINT_URL: str = os.getenv("API_POSTGRESQL_INTERNAL_ENDPOINT_URL", "")
    PROTECTED_ENDPOINT_URL: str = os.getenv("API_POSTGRESQL_PROTECTED_ENDPOINT_URL", "")
    DATABASE_URL: str = os.getenv("API_POSTGRESQL_DATABASE_URL", "")
    SECRET_KEY: str = os.getenv("API_POSTGRESQL_SECRET_KEY", "")
    INTERNAL_SECRET_KEY: str = os.getenv("API_POSTGRESQL_INTERNAL_SECRET_KEY", "")
    ALGORITHM: str = os.getenv("API_POSTGRESQL_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("API_POSTGRESQL_ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    POSTGRESQL_API_POSTGRESQL_CA_PATH: str = os.getenv("POSTGRESQL_API_POSTGRESQL_CA_PATH", "")
    POSTGRESQL_API_POSTGRESQL_CERT_PATH: str = os.getenv("POSTGRESQL_API_POSTGRESQL_CERT_PATH", "")
    POSTGRESQL_API_POSTGRESQL_KEY_PATH: str = os.getenv("POSTGRESQL_API_POSTGRESQL_KEY_PATH", "")
    POSTGRESQL_SERVICE_PORT: str = os.getenv("POSTGRESQL_SERVICE_PORT", "")
    POSTGRESQL_SERVICE_NAME: str = os.getenv("POSTGRESQL_SERVICE_NAME", "")
    POSTGRESQL_USER: str = os.getenv("POSTGRESQL_API_POSTGRESQL_USER", "")
    POSTGRESQL_PASSWORD: str = os.getenv("POSTGRESQL_API_POSTGRESQL_PASSWORD", "")
    POSTGRESQL_DATABASE: str = os.getenv("POSTGRESQL_API_POSTGRESQL_DATABASE", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        secret_key_path = os.getenv("API_POSTGRESQL_INTERNAL_SECRET_KEY_PATH")
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
            print("La variable d'environnement API_POSTGRESQL_INTERNAL_SECRET_KEY_PATH n'est pas définie.")

# Créez une instance de TestSettings pour l'utiliser dans vos tests
test_settings = TestSettings()
