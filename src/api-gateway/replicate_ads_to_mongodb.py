import sys
import time
import os
import random
from fastapi.testclient import TestClient
from main import app

# TODO : passer la réplication dans un container dédié, ne dois pas être dans la Gateway

# Configuration propre du PYTHONPATH (une seule fois, au début du fichier)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test.config.config import config
from test.config.test_settings import test_settings

client = TestClient(app)

# Générer un entier aléatoire entre config.RANDOM_RANGE_START et config.RANDOM_RANGE_END
RND = random.randint(config.RANDOM_RANGE_START, config.RANDOM_RANGE_END)
USERNAME = f"{RND}-flow-user"
EMAIL = f"{USERNAME}@{config.DEFAULT_DOMAIN}"
PASSWORD = USERNAME

LIMIT = 50
BATCH_SIZE = 10

def _signup_and_login():
    # Signup
    response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/signup",
        json={"username": USERNAME, "email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 200, f"Signup a échoué: {response.status_code} {response.text}"

    # Login
    response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/login",
        data={"username": USERNAME, "password": PASSWORD},
    )
    assert response.status_code == 200, f"Login a échoué: {response.status_code} {response.text}"

    token = response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": token,
    }
    return headers
        
def _replicate(headers, limit=50, batch_size=10):
    response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/replicate/ads_to_mongo?limit={limit}&batch_size={batch_size}",
        headers=headers,
    )
    assert response.status_code == 200, f"Replication failed: {response.status_code} {response.text}"
    return response.json()


def main():
    # Signup and connect
    headers = _signup_and_login()

    response = _replicate(headers, LIMIT, BATCH_SIZE)
    print(response)

    
if __name__ == "__main__":
    import sys
    sys.exit(main())
