from typing import Dict, List
from api.clients.client_manager import client_manager

class BackendAuthenticator:
    def __init__(self):
        self.clients = [
            client_manager.get_mongodb_client(),
            client_manager.get_postgresql_client()
            # client_manager.get_other_system_client(),
            # Ajoutez d'autres clients ici
        ]

    def authenticate(self, credentials: Dict[str, str]):
        user_data = {
            "username": credentials.get("username"),
            #"email": credentials.get("email"),
            #"user_id": "12345"
        }

        backend_tokens = {}

        for client in self.clients:
            # Authentifier l'utilisateur sur chaque backend et récupérer les tokens
            token = client.authenticate(credentials)
            backend_tokens[client.name] = token

        # Renvoie les informations de l'utilisateur et les tokens des backends
        return user_data, backend_tokens
