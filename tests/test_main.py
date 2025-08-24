# tests/test_main.py
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Env vars falsas para que main.py no truene al importar
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["FIREBASE_CREDENTIALS"] = "/tmp/fake-creds.json"

# Parches ANTES de importar main
with patch("os.path.exists", return_value=True), \
     patch("firebase_admin.credentials.Certificate") as mock_cert, \
     patch("firebase_admin.initialize_app") as mock_init, \
     patch("firebase_admin.firestore.client") as mock_fs, \
     patch("google.generativeai.GenerativeModel") as mock_model:

    mock_cert.return_value = MagicMock()
    mock_init.return_value = MagicMock()

    # Firestore simulado
    fake_db = MagicMock()
    fake_doc = MagicMock()
    fake_doc.get.return_value.exists = False
    fake_doc.get.return_value.to_dict.return_value = {"messages": []}
    fake_db.collection.return_value.document.return_value = fake_doc
    mock_fs.return_value = fake_db

    # Gemini simulado
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value.text = "Stubbed bot answer"
    mock_model.return_value = mock_instance

    from main import app  # importa después de parchear todo

client = TestClient(app)

def test_chat_endpoint():
    r = client.post("/chat", json={"message": "Is expensive perfume worth it?"})
    assert r.status_code == 200
    data = r.json()
    assert "conversation_id" in data
    assert "message" in data and isinstance(data["message"], list)

def test_chat_empty_message():
    r = client.post("/chat", json={"message": ""})
    assert r.status_code == 422

def test_unique_conversation_id():
    r1 = client.post("/chat", json={"message": "First message"})
    r2 = client.post("/chat", json={"message": "Second message"})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["conversation_id"] != r2.json()["conversation_id"]

def test_long_conversation():
    msgs = ["Hello", "How are you?", "Tell me about perfumes", "Bye!"]
    cid = None
    for m in msgs:
        payload = {"message": m}
        if cid: payload["conversation_id"] = cid
        r = client.post("/chat", json=payload)
        assert r.status_code == 200
        if not cid:
            cid = r.json()["conversation_id"]
        else:
            assert r.json()["conversation_id"] == cid

