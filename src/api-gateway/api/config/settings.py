import os
from pydantic_settings import BaseSettings
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

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
    RSA_PRIVATE_KEY: str = os.getenv("RSA_PRIVATE_KEY", "")  # Valeur par défaut vide

    @classmethod
    def generate_rsa_private_key(cls):
        # Générer une clé privée RSA
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        # Sérialiser la clé en format PEM
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return private_pem.decode('utf-8')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Appel du constructeur parent en premier
        # Générer la clé si elle n'est pas définie
        if not self.RSA_PRIVATE_KEY:
            self.RSA_PRIVATE_KEY = self.generate_rsa_private_key()

settings = Settings()
