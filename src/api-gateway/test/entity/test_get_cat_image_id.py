import sys
import os
import random
from fastapi.testclient import TestClient
from main import app

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

def _create_ad(headers, cat_code, cat_label):
    with open(DEMO_IMAGE_PATH, "rb") as f:
        files = {"file": ("demo_image.jpg", f, "image/jpeg")}
        data = {
            "designation": "Produit flow",
            "description": "Desc flow init",
            "category_code": cat_code,
            "category_label": cat_label,
        }
        response = client.post(
            f"{test_settings.PROTECTED_ENDPOINT_URL}/create_ad",
            headers=headers,
            data=data,
            files=files,
        )
    assert response.status_code == 200, f"Create ad failed: {response.status_code} {response.text}"
    payload = response.json()
    return payload

def test_get_categories_from_image_id():

    headers = _signup_and_login()

    # Create good ad
    ad_data = _create_ad(headers, 2583, "Autour de la piscine")
    image_id = ad_data["image"]["id"]
    
    # Good response
    response = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/get_categories_from_image_id/{image_id}", 
                          headers=headers)
    assert response.status_code == 200, f"Get failed : {response.status_code} {response.text}"
    cat_data = response.json()
    assert cat_data["id"] == 24
    assert cat_data["code"] == 2583
    assert cat_data["label"] == "Autour de la piscine"
    
    # No image
    response = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/get_categories_from_image_id/3000000", 
                          headers=headers)
    assert response.status_code == 500, f"Get failed : {response.status_code} {response.text}"

    # No category associated
    no_cat_ad_data = _create_ad(headers, None, None)
    image_id = no_cat_ad_data["image"]["id"]
    response = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/get_categories_from_image_id/{image_id}", 
                          headers=headers)
    assert response.status_code == 500, f"Get failed : {response.status_code} {response.text}"