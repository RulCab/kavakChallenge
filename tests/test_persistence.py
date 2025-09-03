def test_conversation_persists_in_memory(client):
    # 1) Primer mensaje: fija la postura
    r1 = client.post("/chat", json={"message": "Convénceme de que Coca-Cola es mejor que Pepsi"})
    assert r1.status_code == 200
    cid = r1.json()["conversation_id"]

    # 2) Segundo mensaje en el mismo hilo
    r2 = client.post("/chat", json={"conversation_id": cid, "message": "¿por qué?"})
    assert r2.status_code == 200
    msgs = r2.json()["message"]

    # 3) Debe seguir defendiendo la misma claim
    assert any("Coca-Cola es mejor que Pepsi" in m["message"] for m in msgs if m["role"] == "bot")
