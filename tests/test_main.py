from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post("/chat", json={"message": "Is expensive perfume worth it?"})
    assert response.status_code == 200
    assert "conversation_id" in response.json()
    assert "messages" in response.json()
    assert isinstance(response.json()["messages"], list)
