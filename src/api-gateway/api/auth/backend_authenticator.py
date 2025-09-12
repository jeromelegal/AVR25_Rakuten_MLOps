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


        backend_tokens = {}
        backend_uid = {}
        concat_uid = ""
        for client in self.clients:
            # Authentifier l'utilisateur sur chaque backend et récupérer les tokens
            user_id, token  = client.authenticate(credentials)
            print(f"client.name:{client.name}\n token:\n{token}  ")
            backend_tokens[client.name] = token
            backend_uid[client.name] = user_id
            concat_uid += f"_{user_id}"
        
        user_data = {
            "user_id": concat_uid,
        }        

        # Renvoie les informations de l'utilisateur et les tokens des backends
        return user_data, backend_tokens, backend_uid
