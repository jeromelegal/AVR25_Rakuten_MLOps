# import sys
# import os

# from fastapi.testclient import TestClient

# # Ajouter le chemin absolu de l'application
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '/app')))

# from main import app
# from api.config.settings import settings

# client = TestClient(app)

# def test_add_ad():
#     response = client.post(f"{settings.API_GATEWAY_PROTECTED_ENDPOINT_URL}/create_ad", json={
#         "title": "Test Ad",
#         "description": "This is a test ad",
#         "price": 100,
#         "category_code": "cat1"
#     })
#     assert response.status_code == 200
#     payload = response.json()
#     assert isinstance(payload, list)
#     assert {"code","label"}.issubset(payload[0].keys())
#     assert payload["title"] == "Test Ad"
#     assert payload["description"] == "This is a test ad"
#     assert payload["price"] == 100
#     assert payload["category_code"] == "cat1"

