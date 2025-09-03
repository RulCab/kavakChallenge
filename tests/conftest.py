import os, sys
import pytest
from fastapi.testclient import TestClient

# Asegura que el repo root esté en sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---- Desactiva dependencias externas para tests ----
os.environ["DISABLE_GEMINI"] = "1"
os.environ["DISABLE_FIREBASE"] = "1"

from app.main import app

@pytest.fixture(scope="module")
def client():
    """Fixture para tener un TestClient en todos los tests."""
    return TestClient(app)
