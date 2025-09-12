import os
import requests
from typing import Dict
from api.config.settings import settings


class OtherSystemClient:
    def __init__(self):
        self.name = "other_system"
        self.base_url = os.getenv('OTHER_SYSTEM_BASE_URL')
        # self.internal_api_token = create_access_token({"scope": "internal"})
        self.internal_api_token = None

    def get_headers(self):
        return {
            "Referer": f"{settings.HOST}{settings.PROTECTED_ENDPOINT_URL}",
            "X-API-Key": self.internal_api_token
        }

    def authenticate(self, credentials: Dict[str, str]) -> str:
        headers = self.get_headers()
        response = requests.post(f"{self.base_url}/auth", json=credentials, headers=headers)
        response.raise_for_status()
        return response.json().get("token")
