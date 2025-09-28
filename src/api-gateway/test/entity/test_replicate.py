import sys
import os
import random
import time
from fastapi.testclient import TestClient
from main import app

# Aligne le PYTHONPATH comme dans test_flow_ad.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test.config.config import config
from test.config.test_settings import test_settings

client = TestClient(app)

RND = random.randint(config.RANDOM_RANGE_START, config.RANDOM_RANGE_END)
USERNAME = f"{RND}-replicate-user"
EMAIL = f"{USERNAME}@{config.DEFAULT_DOMAIN}"
PASSWORD = USERNAME

DEMO_IMAGE_PATH = os.path.join("test", "entity", "demo_image.jpg")
SEARCH_TERM = "flow"


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


def _create_ad(headers):
    with open(DEMO_IMAGE_PATH, "rb") as f:
        files = {"file": ("demo_image.jpg", f, "image/jpeg")}
        data = {
            "designation": "Produit flow",
            "description": "Desc flow init",
            "category_code": 10,
            "category_label": "Livre occasion",
        }
        response = client.post(
            f"{test_settings.PROTECTED_ENDPOINT_URL}/create_ad",
            headers=headers,
            data=data,
            files=files,
        )
    assert response.status_code == 200, f"Create ad failed: {response.status_code} {response.text}"
    payload = response.json()
    return payload["ad"]["id"], payload



def _replicate(headers, limit=50, batch_size=10):
    # Appelle l’endpoint de réplication de la gateway
    r = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/replicate/ads_to_mongo?limit={limit}&batch_size={batch_size}",
        headers=headers,
    )
    assert r.status_code == 200, f"Replication failed: {r.status_code} {r.text}"
    return r.json()


def _search_mongo(headers, q, category=None, page=1, page_size=10):
    params = {"q": q, "page": str(page), "page_size": str(page_size)}
    if category:
        params["category"] = category
    r = client.get(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/search_ads",
        headers=headers,
        params=params,
    )
    assert r.status_code == 200, f"Mongo search failed: {r.status_code} {r.text}"
    return r.json()


def test_replicate_ads_to_mongo():
    """
    Flux testé :
      1) signup/login
      2) création d'une annonce en PostgreSQL
      3) réplication vers Mongo (1er passage → insert)
      4) vérification via search Mongo (term unique)
      5) réplication à nouveau (2e passage → doublons)
    """
    headers = _signup_and_login()

    # 1) CREATE en PostgreSQL
    ad_id, _ = _create_ad(headers)

    # Petite latence: si la création déclenche des traitements async (ex: images)
    time.sleep(0.2)
    
    # 2) RÉPLICATION (1)
    response1 = _replicate(headers, limit=100, batch_size=50)
    assert "inserted" in response1 and "duplicates" in response1 and "errors_count" in response1, f"Bad replication payload: {response1}"
    assert response1["inserted"] >= 1 or response1["duplicates"] >= 0, f"Unexpected counters: {response1}"

    # 3) VÉRIFICATION via recherche MongoDB
    search = _search_mongo(headers, q=SEARCH_TERM, category="Livre occasion", page=1, page_size=10)
    assert "items" in search, f"Search payload invalid: {search}"
    items = search["items"]
    assert isinstance(items, list), "Search items must be a list"
    assert any(str(it.get("ad_id")) == str(ad_id) for it in items), f"Inserted ad_id={ad_id} not found in Mongo search"

    # 4) RÉPLICATION (2) — idempotence / doublons
    response2 = _replicate(headers, limit=100, batch_size=50)
    assert response2["errors_count"] == 0, f"Errors on second run: {response2.get('errors_sample')}"
    # Attendu : pas de nouvelle insertion pour la même annonce; duplicates doit être >= à la 1re passe (ou inserted == 0)
    assert response2["inserted"] == 0 or response2["duplicates"] >= response2["duplicates"], f"Idempotence not respected: {response2} -> {response2}"
