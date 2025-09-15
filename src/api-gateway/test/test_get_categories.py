# import sys
# import os
# from fastapi.testclient import TestClient

# # Ajouter le chemin absolu de l'application
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '/app')))

# from main import app
# from api.config.settings import settings

# client = TestClient(app)

# def test_get_categories():
#     response = client.get(f"{settings.API_GATEWAY_PROTECTED_ENDPOINT_URL}/get_categories")
#     assert response.status_code == 200
#     payload = response.json()
#     assert isinstance(payload, list)
#     assert {"code","label"}.issubset(payload[0].keys())