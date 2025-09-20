# /app/test/entity/test_user.py
import sys
import os
from fastapi.testclient import TestClient
from main import app
import random


# Configuration propre du PYTHONPATH (une seule fois, au début du fichier)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test.config.config import config
from test.config.test_settings import test_settings

# Générer un entier aléatoire entre config.RANDOM_RANGE_START et config.RANDOM_RANGE_END
nombre_aleatoire = random.randint(config.RANDOM_RANGE_START, config.RANDOM_RANGE_END)

# Variables pour les informations d'identification de l'utilisateur
username = f"{nombre_aleatoire}newuser-gateway-delete"
email = f"{username}@{config.DEFAULT_DOMAIN}"
password = f"{username}"


client = TestClient(app)

designation = "Test_designation"
description = "Test_description"

def test_create_ad():
    # Inscrire l'utilisateur pour pouvoir le connecter et le supprimer
    signup_response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/signup",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert signup_response.status_code == 200
    
    login_response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/login",
        data={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Récupérer le token d'accès à partir de la réponse de connexion
    access_token = login_response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": access_token,
    }

    with open(
            os.path.join("test", "entity", "demo_image.jpg"), "rb") as f:
        files = {
        "file": ("demo_image.jpg", f, "image/jpeg")
        }
        data = {
            "designation": "Mon super produit",
            "description": "Une description",
            "category_code": 42,
            "category_label": "Gadgets",
        }
        create_ad_response = client.post(
            f"{test_settings.PROTECTED_ENDPOINT_URL}/create_ad",
            headers=headers,
            data=data,
            files=files
        )
    assert create_ad_response.status_code == 200
    print("END ??")
    # Supprimer l'utilisateur seulement de PostgreSQL
    # delete_response = client.delete(
    #     f"{test_settings.PROTECTED_ENDPOINT_URL}/delete/postgresql",
    #     headers=headers
    # )

    # assert delete_response.status_code == 200
    # assert delete_response.json()["message"] == "User deleted successfully from PostgreSQL"