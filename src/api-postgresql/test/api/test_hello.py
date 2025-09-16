import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '/app')))

from main import app
from config.db import get_db

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
