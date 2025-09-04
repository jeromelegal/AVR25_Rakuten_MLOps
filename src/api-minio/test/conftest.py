from unittest.mock import Mock
import pytest
import os

# import os
# import sys
# from fastapi.testclient import TestClient

# # Ajouter le chemin absolu de l'application
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "/app")))

# from main import app
# from api.config.settings import settings

# client = TestClient(app)


@pytest.fixture(scope="function")
def mock_settings():
    mock = Mock()
    mock.MINIO_SERVICE_NAME = os.getenv("MINIO_SERVICE_NAME", default="localhost")
    mock.MINIO_SERVICE_PORT = os.getenv("MINIO_SERVICE_PORT", default="9010")
    mock.MINIO_USER = os.getenv("MINIO_USER", default="minio-user")
    mock.MINIO_PASSWORD = os.getenv("MINIO_PASSWORD", default="minio-password")
    return mock
