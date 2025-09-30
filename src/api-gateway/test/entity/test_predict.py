import sys
import os
import random
from fastapi.testclient import TestClient
from main import app

# Configuration propre du PYTHONPATH
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from test.config.config import config
from test.config.test_settings import test_settings

client = TestClient(app)

# Générer un utilisateur unique
RND = random.randint(config.RANDOM_RANGE_START, config.RANDOM_RANGE_END)
USERNAME = f"{RND}-flow-user"
EMAIL = f"{USERNAME}@{config.DEFAULT_DOMAIN}"
PASSWORD = USERNAME

DEMO_IMAGE_PATH = os.path.join("test", "entity", "demo_image.jpg")


def _signup_and_login():
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


def test_predict_success():
    """Test d’un appel valide avec description + image"""
    headers = _signup_and_login()

    with open(DEMO_IMAGE_PATH, "rb") as f:
        response = client.post(
            f"{test_settings.PROTECTED_ENDPOINT_URL}/api-processing/predict",
            headers=headers,
            data={
                "description": "Robot aspirateur de piscine",
                "designation": "Robot aspirateur NETOWATOU 3000",
            },
            files={"files": ("demo_image.jpg", f, "image/jpeg")},
        )

    assert (
        response.status_code == 200
    ), f"Predict failed: {response.status_code} {response.text}"
    payload = response.json()

    # Vérifie que la réponse contient bien les champs attendus
    assert "category" in payload
    assert "probability" in payload
    assert "overall_probabilities" in payload
