# tests/e2e/gateway/test_search_mongodb.py
import sys
import os
import random
from fastapi.testclient import TestClient
from main import app

# test/entity/test_search_mongodb.py
import sys, os, random
from fastapi.testclient import TestClient

# Aligne le PYTHONPATH comme dans test_flow_ad.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app
from test.config.config import config
from test.config.test_settings import test_settings

client = TestClient(app)

# Utilisateur jetable (même pattern que test_flow_ad)
RND = random.randint(config.RANDOM_RANGE_START, config.RANDOM_RANGE_END)
USERNAME = f"{RND}-search-user"
EMAIL = f"{USERNAME}@{config.DEFAULT_DOMAIN}"
PASSWORD = USERNAME


def _signup_and_login():
    # Signup
    r = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/signup",
        json={"username": USERNAME, "email": EMAIL, "password": PASSWORD},
    )
    assert r.status_code == 200, f"Signup échoué: {r.status_code} {r.text}"

    # Login
    r = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/login",
        data={"username": USERNAME, "password": PASSWORD},
    )
    assert r.status_code == 200, f"Login échoué: {r.status_code} {r.text}"
    token = r.json()["access_token"]

    # Headers attendus par la gateway
    return {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": token,
    }


def _assert_search_shape(p):
    assert isinstance(p, dict)
    for k in ("items", "count", "page", "page_size", "has_more"):
        assert k in p
    assert isinstance(p["items"], list)
    assert isinstance(p["count"], int)
    assert isinstance(p["page"], int) and p["page"] >= 1
    assert isinstance(p["page_size"], int) and 1 <= p["page_size"] <= 50
    assert isinstance(p["has_more"], bool)


def test_gateway_search_ads_minimal():
    """
    Fumée Gateway sans hypothèse de seed :
    - GET /protected/mongodb/search_ads : 200 + structure
    - Pagination page=1 / page=2
    - Si un item existe, GET /protected/mongodb/ad/{mongo_id}
    - Si image présente, GET /protected/minio/image/{image_uuid}
    """
    headers = _signup_and_login()

    # 1) Appel simple
    r = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/search_ads", headers=headers)
    assert r.status_code == 200, f"search_ads failed: {r.status_code} {r.text}"
    payload = r.json()
    _assert_search_shape(payload)

    first = payload["items"][0] if payload["items"] else None

    # 2) Pagination
    r1 = client.get(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/search_ads",
        headers=headers, params={"page": 1, "page_size": 1}
    )
    assert r1.status_code == 200, r1.text
    p1 = r1.json(); _assert_search_shape(p1); assert p1["page"] == 1 and p1["page_size"] == 1

    r2 = client.get(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/search_ads",
        headers=headers, params={"page": 2, "page_size": 1}
    )
    assert r2.status_code == 200, r2.text
    p2 = r2.json(); _assert_search_shape(p2); assert p2["page"] == 2 and p2["page_size"] == 1

    if p1["items"] and p2["items"]:
        assert len(p1["items"]) == 1 and len(p2["items"]) == 1

    # 3) Détail d'une annonce si dispo
    if first:
        mid = first["id"]
        r = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/ad/{mid}", headers=headers)
        assert r.status_code == 200, r.text
        ad = r.json()
        for k in ("id", "ad_id", "user", "designation", "category", "created_at"):
            assert k in ad
        assert "username" in ad["user"]

        # 4) Image MinIO si dispo
        images = ad.get("images") or first.get("images") or []
        if images and images[0].get("image_uuid"):
            img_uuid = images[0]["image_uuid"]
            r = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/image/{img_uuid}", headers=headers)
            assert r.status_code == 200, r.text
            img = r.json()
            assert "content" in img and isinstance(img["content"], str) and len(img["content"]) > 0
            assert "content_type" in img
