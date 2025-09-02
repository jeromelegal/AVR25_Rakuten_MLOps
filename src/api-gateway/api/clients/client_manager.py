from api.clients.mongodb_client import MongoDBClient
from api.clients.postgresql_client import PostgreSQLClient
from api.clients.other_system_client import OtherSystemClient

class ClientManager:
    def __init__(self):
        self.mongodb_client = MongoDBClient()
        self.postgresql_client = PostgreSQLClient()
        #self.other_system_client = OtherSystemClient()

    def get_mongodb_client(self):
        return self.mongodb_client

    def get_postgresql_client(self):
        return self.postgresql_client

    def get_other_system_client(self):
        return self.other_system_client

# Initialiser les clients au démarrage
client_manager = ClientManager()
