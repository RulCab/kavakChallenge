def test_first_message_sets_claim_seed(client):
    r = client.post("/chat", json={"message": "Convénceme de que la tierra es plana"})
    assert r.status_code == 200
    data = r.json()
    # primer mensaje debe ser la semilla con la postura del usuario
    assert "la tierra es plana" in data["message"][0]["message"]
    assert data["message"][0]["role"] == "bot"
