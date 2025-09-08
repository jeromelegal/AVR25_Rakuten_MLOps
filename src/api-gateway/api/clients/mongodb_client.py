import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError
from urllib3.util.ssl_ import create_urllib3_context
from typing import Optional, Dict
from api.config.settings import settings
from api.auth.token_manager import create_access_token


class MongoDBClient:
    def __init__(self):
        self.name = "mongodb"
        self.base_url = settings.API_MONGODB_BASE_URL
        self.ca_path = settings.API_MONGODB_API_GATEWAY_CA_PATH
        self.key_path = settings.API_MONGODB_API_GATEWAY_KEY_PATH
        self.cert_path = settings.API_MONGODB_API_GATEWAY_CERT_PATH
        self.internal_api_token = create_access_token({"scope": "internal"})
        self.session = self.get_session()

    def get_session(self):
        session = requests.Session()

        class MTLSAdapter(HTTPAdapter):
            def __init__(self, ca_path, key_path, cert_path, *args, **kwargs):
                self.ca_path = ca_path
                self.key_path = key_path
                self.cert_path = cert_path
                super().__init__(*args, **kwargs)

            def init_poolmanager(self, *args, **kwargs):
                context = create_urllib3_context()
                context.load_verify_locations(cafile=self.ca_path)
                context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
                kwargs["ssl_context"] = context
                return super().init_poolmanager(*args, **kwargs)

        session.mount(
            "https://", MTLSAdapter(self.ca_path, self.key_path, self.cert_path)
        )
        return session

    def get_headers(self):
        return {
            "Referer": f"{settings.HOST}{settings.PROTECTED_ENDPOINT_URL}",
            "X-API-Key": self.internal_api_token,
        }

    def authenticate(self, credentials: Dict[str, str]) -> Optional[str]:
        headers = self.get_headers()
        try:
            response = self.session.post(
                f"{self.base_url}/token", data=credentials, headers=headers
            )
            response.raise_for_status()
            return response.json().get("access_token")
        except HTTPError as e:
            return None
            # if e.response.status_code == 401:
            #     # Gérer le cas où l'utilisateur n'existe pas ou les informations d'identification sont incorrectes
            #     return None
            # else:
            #     # Gérer d'autres erreurs HTTP
            #     raise

    def get_user_by_email(self, email: str):
        headers = self.get_headers()
        response = self.session.get(
            f"{self.base_url}/api/internal/mongodb/entity/user?email={email}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def create_user(self, user_data: Dict[str, str]):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/user",
            json=user_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def create_ad(self, ad_data: Dict[str, str]):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/ad",
            json=ad_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def get_ad(self, ad_id: str):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/ad/{ad_id}", headers=headers
        )
        response.raise_for_status()
        return response.json()

    def update_ad(self, ad_data: Dict[str, str]):
        headers = self.get_headers()
        ad_id = ad_data["ad_id"]
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/ad/{ad_id}",
            json=ad_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def delete_ad(self, ad_id: str):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/ad/{ad_id}", headers=headers
        )
        response.raise_for_status()
        return response.json()

    def create_category(self, category_data: Dict[str, str]):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/category",
            json=category_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def get_category(self, category_id: str):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/category/{category_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def update_category(self, category_data: Dict[str, str]):
        headers = self.get_headers()
        category_id = category_data["ad_id"]
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/category/{category_id}",
            json=category_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def delete_category(self, category_id: str):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/category/{category_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def create_ad_category(self, ad_category_data: Dict[str, str]):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/ad_category",
            json=ad_category_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def get_ad_category(self, relation_id: str):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/ad_category/{relation_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def update_ad_category(self, ad_category_data: Dict[str, str]):
        headers = self.get_headers()
        relation_id = ad_category_data["ad_id"]
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/ad_category/{relation_id}",
            json=ad_category_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def delete_ad_category(self, relation_id: str):
        headers = self.get_headers()
        response = self.session.post(
            f"{self.base_url}/api/internal/mongodb/entity/ad_category/{relation_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
