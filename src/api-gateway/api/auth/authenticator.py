import logging
from typing import Dict, Tuple
from api.auth.clients.manager import ClientManager, create_client_manager
from config.settings import Settings

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

class BackendAuthenticator:
    def __init__(self, client_manager: ClientManager):
        self.client_manager = client_manager
        # Liste des noms des clients que vous souhaitez utiliser
        # TODO : lors des ajouts d'ACL, ajouter minio
        self.client_names = ["mongodb", "postgresql"]
        self.clients = [self.client_manager.get_client(name) for name in self.client_names]
        logger.debug("BackendAuthenticator initialized with clients: %s", self.client_names)

    def authenticate(self, credentials: Dict[str, str]) -> Tuple[Dict, Dict, Dict]:
        backend_tokens = {}
        backend_uid = {}
        concat_uid = ""

        for client in self.clients:
            client_name = client.__class__.__name__.replace("Client", "").lower()
            logger.debug(f"Attempting to authenticate with {client_name}...")
            # Authentifier l'utilisateur sur chaque backend et récupérer les tokens
            auth_data = client.authenticate(token=None, credentials=credentials)
            if auth_data is not None:
                user_id, token = auth_data.get("user_id"), auth_data.get("access_token")
                logger.debug(f"Authentication successful with {client_name}. User ID: {user_id}")
                backend_tokens[client_name] = token
                backend_uid[client_name] = user_id
                concat_uid += f"_{user_id}"
            else:
                logger.warning(f"Authentication failed with {client_name}")

        if not concat_uid:
            logger.warning("No user IDs were returned from the authentication clients.")
        else:
            logger.debug(f"Concatenated User ID: {concat_uid}")

        user_data = {
            "user_id": concat_uid,
        }
        logger.debug(f"Returning user data: {user_data}")

        # Renvoie les informations de l'utilisateur et les tokens des backends
        return user_data, backend_tokens, backend_uid

def create_backend_authenticator(settings: Settings) -> BackendAuthenticator:
    logger.debug("Creating BackendAuthenticator instance...")
    client_manager = create_client_manager(settings)
    return BackendAuthenticator(client_manager)
