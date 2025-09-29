import sys
import os
import random
from fastapi.testclient import TestClient
from main import app

DEFAULT_BUCKET = "raw-images"

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
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": token,
    }
    return headers

def test_image():
    headers = _signup_and_login()

    with open(DEMO_IMAGE_PATH, "rb") as f:
        files = {"file": ("demo_image.jpg", f, "image/jpeg")}
        res_post = client.post(
            f"{test_settings.PROTECTED_ENDPOINT_URL}/save_image",
            headers=headers,
            files=files,
        )
    assert res_post.status_code == 200, f"Create image failed: {res_post.status_code} {res_post.text}"
    post_json = res_post.json()
    image_uuid = post_json["image_id"]

    bucket = DEFAULT_BUCKET
    res_get = client.get(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/get_image/{bucket}/{image_uuid}",
        headers=headers
    )
    assert res_get.status_code == 200, f"Get failed : {res_get.status_code} {res_get.text}"
    get_json = res_get.json()
    assert get_json["image_id"] == image_uuid

