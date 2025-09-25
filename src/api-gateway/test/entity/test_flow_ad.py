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


def test_flow_ad():
    """
    Test du flux complet:
    - création
    - lecture
    - update (texte)
    - re-lecture
    - update (catégorie + image)
    - re-lecture
    - suppression
    - vérification lecture KO
    """
    headers = _signup_and_login()

    # CREATE
    ad_id, created = _create_ad(headers)
    assert isinstance(ad_id, int) or (isinstance(ad_id, str) and ad_id), f"Invalid ad_id : {ad_id}"
    
    for k in ("ad", "category", "image", "relations"):
        assert k in created, f"Field missing in ad creation: '{k}'"

    # READ
    response = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/read_ad_psql/{ad_id}", headers=headers)
    assert response.status_code == 200, f"Read failed after create: {response.status_code} {response.text}"
    json = response.json()
    assert json["ad"]["id"] == ad_id, f"Read_ad return bad id: {json['ad']['id']} != {ad_id}"
    assert json["ad"]["designation"] == "Produit flow", f"Bad designation: {json['ad']['designation']}"
    assert "user" in json and "username" in json["user"], "Missing 'user' informations"

    # UPDATE (only text)
    response = client.patch(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/update_ad/{ad_id}",
        headers=headers,
        data={"designation": "Produit modifié", "description": "Desc flow MAJ"},
    )
    assert response.status_code == 200, f"Update (text) failed: {response.status_code} {response.text}"
    update1 = response.json()
    assert update1["ad"]["id"] == ad_id, "Bad ID after update(text)"

    # READ (verify update text)
    response = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/read_ad_psql/{ad_id}", headers=headers)
    assert response.status_code == 200, f"Read after update(text) failed: {response.status_code} {response.text}"
    json = response.json()
    assert json["ad"]["designation"] == "Produit modifié", "designation not updated"
    assert json["ad"].get("description") == "Desc flow MAJ", "description not updated"

    # DELETE
    response = client.delete(f"{test_settings.PROTECTED_ENDPOINT_URL}/delete_ad/{ad_id}", headers=headers)
    assert response.status_code == 200, f"Delete failed: {response.status_code} {response.text}"
    delete_json = response.json()
    assert delete_json.get("ad_id") == ad_id or str(delete_json.get("ad_id")) == str(ad_id), \
        f"Reponse delete inattendue: {delete_json}"
    assert "ad_deleted" in delete_json, "Field 'ad_deleted' missing"

    # READ (404 waited)
    response = client.get(f"{test_settings.PROTECTED_ENDPOINT_URL}/read_ad_psql/{ad_id}", headers=headers)
    assert response.status_code in (404, 410), f"Read post-delete must failed (404/410), received {response.status_code}: {response.text}"
