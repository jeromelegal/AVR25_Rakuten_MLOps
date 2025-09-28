from typing import Dict, Optional
import requests
from requests.exceptions import HTTPError

API_GATEWAY_URL = "https://api-gateway"
API_GATEWAY_PROTECTED_ENDPOINT_URL = "/protected"


class APIGatewayClient:
    _username: str
    _password: str
    _base_url: str
    _email: str

    def __init__(
        self, username: str, password: str, email: str, base_url: str = API_GATEWAY_URL
    ):
        self._username = username
        self._password = password
        self._email = email
        self._base_url = base_url
        self._token = None
        self.signup()

    def _post(self, endpoint: str, payload: Dict, include_token: bool = True):
        url = f"{self._base_url}/{endpoint}"
        headers = self._get_headers() if include_token else None

        response = requests.post(url=url, json=payload, headers=headers)

        response.raise_for_status()
        return response.json()

    def _get(self, endpoint: str, params: Optional[Dict] = None):
        url = f"{self._base_url}/{endpoint}"
        headers = self._get_headers()

        response = requests.get(url=url, params=params, headers=headers)

        response.raise_for_status()
        return response.json()

    def signup(self):
        try:
            self._post(
                endpoint=f"{API_GATEWAY_PROTECTED_ENDPOINT_URL}/signup",
                payload={
                    "username": self._username,
                    "password": self._password,
                    "email": self._email,
                },
                include_token=False,
            )
        except HTTPError:
            pass

    def login(self):
        response = self._post(
            endpoint=f"{API_GATEWAY_PROTECTED_ENDPOINT_URL}/login",
            payload={"username": self._username, "password": self._password},
            include_token=False,
        )
        self._token = response.json().get("access_token")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Referer": self._base_url + API_GATEWAY_PROTECTED_ENDPOINT_URL,
            "X-API-Key": self._token,
        }
        return headers

    def get_category_from_image_id(self, image_id) -> Optional[int]:
        response = self._get(
            f"{API_GATEWAY_PROTECTED_ENDPOINT_URL}/get_categories_from_image_id/{image_id}"
        )

        if response.status_code == 200:
            return int(response.get("code"))

        return None
