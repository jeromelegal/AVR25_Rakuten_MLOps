import random

class Config:
    # URL de l'API Gateway
    API_GATEWAY_PROTECTED_ENDPOINT_URL = "http://example.com/api"

    # Plage pour générer un nombre aléatoire
    RANDOM_RANGE_START = 1
    RANDOM_RANGE_END = 100000

    # Domaine par défaut pour les emails
    DEFAULT_DOMAIN = "example.com"

config = Config()
