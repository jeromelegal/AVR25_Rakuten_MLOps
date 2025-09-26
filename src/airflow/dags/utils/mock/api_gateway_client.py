import logging
import random
from typing import Optional

POSIBLE_CATEGORY = [10, 20, 30, 40, None]


class MockAPIGatewayClient:
    _username: str
    _password: str
    _base_url: str
    _email: str

    def __init__(self, username: str, password: str, email: str, base_url: str):
        self._username = username
        self._password = password
        self._email = email
        self._base_url = base_url
        self._token = None

    def signup(self):
        logging.info("Signing up")

    def login(self):
        logging.info("Login")

    def get_category_from_image_id(self, image_id: str) -> Optional[int]:
        return random.choice(POSIBLE_CATEGORY)
