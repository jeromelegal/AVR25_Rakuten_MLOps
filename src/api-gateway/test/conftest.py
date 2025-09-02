import pytest
import sys
import os
from fastapi.testclient import TestClient

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '/app')))

from main import app
from api.config import settings


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
