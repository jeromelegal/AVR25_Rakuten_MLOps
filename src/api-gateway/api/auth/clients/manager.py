import logging
from api.config.settings import Settings
from api.auth.clients.postgresql import PostgreSQLClient
from api.auth.clients.mongodb import MongoDBClient

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

class ClientManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.clients = {}  # Dictionnaire pour stocker tous les clients
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialise et enregistre les clients disponibles."""
        self.register_client("mongodb", MongoDBClient(self.settings))
        self.register_client("postgresql", PostgreSQLClient(self.settings))
        logger.debug("Initialized clients: %s", list(self.clients.keys()))

    def register_client(self, name: str, client):
        """Enregistre un nouveau client."""
        self.clients[name] = client
        logger.debug("Registered client: %s", name)

    def get_client(self, name: str):
        """Retourne un client par son nom."""
        client = self.clients.get(name)
        if client is None:
            logger.error("Client not found: %s", name)
            raise ValueError(f"Client '{name}' not found.")
        return client

def create_client_manager(settings: Settings):
    """Crée et retourne une instance de ClientManager."""
    return ClientManager(settings)
