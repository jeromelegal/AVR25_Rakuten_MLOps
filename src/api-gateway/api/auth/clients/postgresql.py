import logging
import os.path
from requests import Session, HTTPError
from urllib3.util.ssl_ import create_urllib3_context
from requests.adapters import HTTPAdapter
from typing import Optional, Dict, Any
from config.settings import Settings

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class MTLSAdapter(HTTPAdapter):
    def __init__(self, ca_path: str, key_path: str, cert_path: str, *args, **kwargs):
        self.ca_path = ca_path
        self.key_path = key_path
        self.cert_path = cert_path
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.load_verify_locations(cafile=self.ca_path)
        context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

# TODO : variabiliser entity/relation dans les fonctions CRUD 
class PostgreSQLClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _check_file_existence(self, file_path: str, description: str) -> None:
        """Vérifie l'existence d'un fichier et log une erreur si non trouvé."""
        if not os.path.exists(file_path):
            logger.error(f"{description} file not found: '{file_path}'")
            raise FileNotFoundError(f"{description} file not found: '{file_path}'")

    def get_session(self) -> Session:
        """ Crée une session avec les configurations SSL/TLS nécessaires. """
        ca_path = self.settings.API_POSTGRESQL_API_GATEWAY_CA_PATH
        key_path = self.settings.API_POSTGRESQL_API_GATEWAY_KEY_PATH
        cert_path = self.settings.API_POSTGRESQL_API_GATEWAY_CERT_PATH
        # Vérification de l'existence des fichiers
        self._check_file_existence(ca_path, "CA certificate")
        self._check_file_existence(key_path, "Key")
        self._check_file_existence(cert_path, "Certificate")
        session = Session()
        adapter = MTLSAdapter(ca_path=ca_path, key_path=key_path, cert_path=cert_path)
        session.mount("https://", adapter)
        return session

    def get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """ Génère les en-têtes pour la requête HTTP. """
        headers = {
            "Referer": f"{self.settings.API_GATEWAY_HOST}{self.settings.INTERNAL_ENDPOINT_URL}",
        }
        if token:
            headers.update({
                "X-API-Key": token,
                "Authorization": f"Bearer {token}"
            })
        return headers

    def authenticate(self, token: Optional[str], credentials: Dict[str, str]) -> Optional[Dict[str, str]]:
        """ Authentifie un utilisateur. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()
        try:
            response = session.post(f"{base_url}/token", data=credentials, headers=headers)
            logger.debug(f"Authentication Response Status Code: {response.status_code}")
            logger.debug(f"Authentication Response Content: {response.text}")
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            logger.error(f"Authentication error: {e}")
            return None

    def create_entity(self, token: str, table: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """ Crée une nouvelle entité dans la table spécifiée. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()

        endpoint = f"{base_url}/api/internal/postgresql/entity/{table}"
        logger.debug(f"Request URL: {endpoint}")
        logger.debug(f"Request Headers: {headers}")
        logger.debug(f"Request Data: {entity_data}")

        response = session.post(endpoint, json=entity_data, headers=headers)
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")
        response.raise_for_status()

        return response.json()

    def read_entity(self, token: str, table: str, entity_id: int) -> Dict[str, Any]:
        """ Lit une entité de la table spécifiée. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()

        endpoint = f"{base_url}/api/internal/postgresql/entity/{table}/{entity_id}"
        logger.debug(f"Request URL: {endpoint}")

        response = session.get(endpoint, headers=headers)
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")
        response.raise_for_status()

        return response.json()

    def update_entity(self, token: str, table: str, entity_id: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """ Met à jour une entité dans la table spécifiée. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()

        endpoint = f"{base_url}/api/internal/postgresql/entity/{table}/{entity_id}"
        logger.debug(f"Request URL: {endpoint}")
        logger.debug(f"Request Data: {entity_data}")

        response = session.put(endpoint, json=entity_data, headers=headers)
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")
        response.raise_for_status()

        return response.json()

    def delete_entity(self, token: str, table: str, entity_id: int) -> Dict[str, Any]:
        """ Supprime une entité de la table spécifiée. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()

        endpoint = f"{base_url}/api/internal/postgresql/entity/{table}/{entity_id}"
        logger.debug(f"Request URL: {endpoint}")

        response = session.delete(endpoint, headers=headers)
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")
        response.raise_for_status()

        return response.json()

# TODO : variabiliser entity/relation dans les fonctions CRUD 
    def create_relation(self, token: str, table: str, relation_data: Dict[str, Any]) -> Dict[str, Any]:
        """ Crée une nouvelle relation dans la table spécifiée. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()

        endpoint = f"{base_url}/api/internal/postgresql/relation/{table}"
        logger.debug(f"Request URL: {endpoint}")
        logger.debug(f"Request Headers: {headers}")
        logger.debug(f"Request Data: {relation_data}")

        response = session.post(endpoint, json=relation_data, headers=headers)
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")
        response.raise_for_status()

        return response.json()

    def read_relation(self, token: str, table: str, relation_id: int) -> Dict[str, Any]:
        """ Lit une relation de la table spécifiée. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()

        endpoint = f"{base_url}/api/internal/postgresql/relation/{table}/{relation_id}"
        logger.debug(f"Request URL: {endpoint}")

        response = session.get(endpoint, headers=headers)
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")
        response.raise_for_status()

        return response.json()

    def delete_relation(self, token: str, table: str, relation_id: int) -> Dict[str, Any]:
        """ Supprime une relation de la table spécifiée. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()

        endpoint = f"{base_url}/api/internal/postgresql/relation/{table}/{relation_id}"
        logger.debug(f"Request URL: {endpoint}")

        response = session.delete(endpoint, headers=headers)
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")
        response.raise_for_status()

        return response.json()
    
    def read_categories(self, token: str, table: str) -> Dict[str, Any]:
        """ Liste les catégories en base. """
        base_url = self.settings.API_POSTGRESQL_BASE_URL
        headers = self.get_headers(token)
        session = self.get_session()

        endpoint = f"{base_url}/api/internal/postgresql/entity/{table}"
        logger.debug(f"Request URL: {endpoint}")

        response = session.get(endpoint, headers=headers)
        logger.debug(f"Response Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text}")
        response.raise_for_status()

        return response.json()

