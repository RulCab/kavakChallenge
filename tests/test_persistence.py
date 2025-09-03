def test_conversation_persists_in_memory(client):
    # simulamos: mismo CID, varias llamadas
    r1 = client.post("/chat", json={"message": "Coca-Cola > Pepsi"})
    cid = r1.json()["conversation_id"]

    r2 = client.post("/chat", json={"conversation_id": cid, "message": "¿por qué?"})
    assert r2.status_code == 200
    msgs = r2.json()["message"]
    # debe contener al menos un mensaje anterior
    assert any("Coca-Cola" in m["message"] for m in msgs)
