from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

import logging

logging.getLogger("google.auth.transport").setLevel(logging.CRITICAL)

# Agregar la raíz del proyecto al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock de Firestore
mock_firestore = MagicMock()
mock_firestore.collection.return_value.document.return_value.get.return_value.to_dict.return_value = {
    "messages": []
}


with patch("firebase_admin.credentials.Certificate") as mock_cert, \
     patch("firebase_admin.initialize_app") as mock_init, \
     patch("firebase_admin.firestore.client", return_value=mock_firestore):

    mock_cert.return_value = MagicMock()
    mock_init.return_value = MagicMock()  # Evita que Firebase se inicialice

    from main import app  # Importar después del mock

client = TestClient(app)

def test_chat_endpoint():
    response = client.post("/chat", json={"message": "Is expensive perfume worth it?"})
    assert response.status_code == 200
    assert "conversation_id" in response.json()
    assert "message" in response.json()
    assert isinstance(response.json()["message"], list)

# ✅ Test 2: Verifica que la API responde con error si el mensaje está vacío
def test_chat_empty_message():
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422 # Código de error esperado para una solicitud inválida

# ✅ Test 3: Verifica que la API devuelve un ID de conversación único en cada request
def test_unique_conversation_id():
    response1 = client.post("/chat", json={"message": "First message"})
    response2 = client.post("/chat", json={"message": "Second message"})
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["conversation_id"] != response2.json()["conversation_id"]

# ✅ Test 4: Probar una conversación más larga con múltiples mensajes
def test_long_conversation():
    messages = ["Hello", "How are you?", "Tell me about perfumes", "Bye!"]
    conversation_id = None

    for msg in messages:
        payload = {"message": msg}
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        assert "conversation_id" in response.json()
        assert "message" in response.json()

        if conversation_id is None:
            conversation_id = response.json()["conversation_id"]
        else:
            assert conversation_id == response.json()["conversation_id"]  # Asegurar que es la misma conversación
