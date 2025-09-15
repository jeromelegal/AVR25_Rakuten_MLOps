from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    API_GATEWAY_HOST: str = os.getenv("API_GATEWAY_HOST", "")
    INTERNAL_ENDPOINT_URL: str = os.getenv("API_MONGODB_INTERNAL_ENDPOINT_URL", "")
    PROTECTED_ENDPOINT_URL: str = os.getenv("API_MONGODB_PROTECTED_ENDPOINT_URL", "")
    DATABASE_URL: str = os.getenv("API_MONGODB_DATABASE_URL", "")
    SECRET_KEY: str = os.getenv("API_MONGODB_SECRET_KEY", "")
    INTERNAL_SECRET_KEY: str = os.getenv("API_MONGODB_INTERNAL_SECRET_KEY", "")
    ALGORITHM: str = os.getenv("API_MONGODB_ALGORITHM", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("API_MONGODB_ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Valeur par défaut de 30 minutes
    MONGODB_API_MONGODB_CA_PATH: str = os.getenv("MONGODB_API_MONGODB_CA_PATH", "")
    MONGODB_API_MONGODB_PEM_PATH: str = os.getenv("MONGODB_API_MONGODB_PEM_PATH", "")
    MONGODB_SERVICE_PORT: str = os.getenv("MONGODB_SERVICE_PORT", "")
    MONGODB_SERVICE_NAME: str = os.getenv("MONGODB_SERVICE_NAME", "")
    MONGODB_USER: str = os.getenv("MONGODB_API_MONGODB_USER", "")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_API_MONGODB_PASSWORD", "")
    MONGODB_DATABASE: str = os.getenv("MONGODB_API_MONGODB_DATABASE", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ajoutez ici votre logique supplémentaire pour certaines variables si nécessaire
        secret_key_path = os.getenv("INTERNAL_SECRET_KEY_PATH")
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
            print("La variable d'environnement INTERNAL_SECRET_KEY_PATH n'est pas définie.")


            
settings = Settings()
