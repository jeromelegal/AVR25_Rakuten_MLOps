import os
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    API_GATEWAY_HOST: str = os.getenv("API_GATEWAY_HOST", "http://test-gateway")
    INTERNAL_ENDPOINT_URL: str = os.getenv("API_MONGODB_INTERNAL_ENDPOINT_URL", "/internal")
    PROTECTED_ENDPOINT_URL: str = os.getenv("API_MONGODB_PROTECTED_ENDPOINT_URL", "/protected")
    DATABASE_URL: str = os.getenv("API_MONGODB_DATABASE_URL", "mongodb://localhost:27017")
    SECRET_KEY: str = os.getenv("API_MONGODB_SECRET_KEY", "test-secret-key")
    INTERNAL_SECRET_KEY: str = os.getenv("API_MONGODB_INTERNAL_SECRET_KEY", "test-internal-secret-key")
    ALGORITHM: str = os.getenv("API_MONGODB_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("API_MONGODB_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    MONGODB_API_MONGODB_CA_PATH: str = os.getenv("MONGODB_API_MONGODB_CA_PATH", "/etc/ssl/api-mongodb/mongdb_api-mongodb.ca")
    MONGODB_API_MONGODB_PEM_PATH: str = os.getenv("MONGODB_API_MONGODB_PEM_PATH", "/path/to/test/client.pem")
    MONGODB_SERVICE_PORT: str = os.getenv("MONGODB_SERVICE_PORT", "27017")
    MONGODB_SERVICE_NAME: str = os.getenv("MONGODB_SERVICE_NAME", "localhost")
    MONGODB_USER: str = os.getenv("MONGODB_API_MONGODB_USER", "testuser")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_API_MONGODB_PASSWORD", "testpass")
    MONGODB_DATABASE: str = os.getenv("MONGODB_API_MONGODB_DATABASE", "testdb")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ajoutez ici votre logique supplémentaire pour certaines variables si nécessaire
        secret_key_path = os.getenv("API_MONGODB_INTERNAL_SECRET_KEY_PATH")
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
            print("La variable d'environnement API_MONGODB_INTERNAL_SECRET_KEY_PATH n'est pas définie.")

# Créez une instance de TestSettings pour l'utiliser dans vos tests
test_settings = TestSettings()
