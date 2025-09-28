from typing import Dict, Optional
import requests

API_GATEWAY_URL = "https://api-gateway"


class APIGatewayClient:
    _username: str
    _password: str
    _base_url: str

    def __init__(self, username: str, password: str, base_url: str = API_GATEWAY_URL):
        self._username = username
        self._password = password
        self._base_url = base_url
        self._token = self._get_token()

    def signup(self):
        raise NotImplementedError()

    def login(self):
        raise NotImplementedError()

    def _get_token(self):
        raise NotImplementedError()

    def _get_header(self) -> Dict[str, str]:
        raise NotImplementedError()

    def get_category_from_image_id(self) -> Optional[int]:
        raise NotImplementedError()

    def _signup_and_login(self):
        # Signup
        r = client.post(
            f"{test_settings.PROTECTED_ENDPOINT_URL}/signup",
            json={"username": USERNAME, "email": EMAIL, "password": PASSWORD},
        )
        assert r.status_code == 200, f"Signup a échoué: {r.status_code} {r.text}"

        # Login
        r = client.post(
            f"{test_settings.PROTECTED_ENDPOINT_URL}/login",
            data={"username": USERNAME, "password": PASSWORD},
        )
        assert r.status_code == 200, f"Login a échoué: {r.status_code} {r.text}"

        token = r.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST
            + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": token,
        }
        return headers
