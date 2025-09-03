def test_chat_endpoint(client):
    r = client.post("/chat", json={"message": "Is expensive perfume worth it?"})
    assert r.status_code == 200
    data = r.json()
    assert "conversation_id" in data
    assert "message" in data and isinstance(data["message"], list)


def test_chat_empty_message(client):
    r = client.post("/chat", json={"message": ""})
    assert r.status_code == 422


def test_unique_conversation_id(client):
    r1 = client.post("/chat", json={"message": "First message"})
    r2 = client.post("/chat", json={"message": "Second message"})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["conversation_id"] != r2.json()["conversation_id"]


def test_long_conversation(client):
    msgs = ["Hello", "How are you?", "Tell me about perfumes", "Bye!"]
    cid = None
    for m in msgs:
        payload = {"message": m}
        if cid:
            payload["conversation_id"] = cid
        r = client.post("/chat", json=payload)
        assert r.status_code == 200
        if not cid:
            cid = r.json()["conversation_id"]
        else:
            assert r.json()["conversation_id"] == cid


def test_returns_last_five_messages_in_order(client, monkeypatch):
    mem_store: dict[str, list[dict]] = {}

    def _fake_load(cid: str):
        return mem_store.get(cid, [])

    def _fake_save(cid: str, msgs: list[dict]):
        mem_store[cid] = list(msgs)

    # parcheamos load/save dentro de routes
    monkeypatch.setattr("app.api.routes.load_conversation", _fake_load)
    monkeypatch.setattr("app.api.routes.save_conversation", _fake_save)

    cid = None
    for i in range(7):
        payload = {"message": f"msg_{i}"}
        if cid:
            payload["conversation_id"] = cid
        r = client.post("/chat", json=payload)
        assert r.status_code == 200
        if not cid:
            cid = r.json()["conversation_id"]

    last = client.post("/chat", json={"conversation_id": cid, "message": "final"})
    assert last.status_code == 200
    resp = last.json()

    # Debe devolver exactamente 5 mensajes
    assert "message" in resp and isinstance(resp["message"], list)
    assert len(resp["message"]) == 5

    # Debe coincidir con los 5 últimos guardados
    assert resp["message"] == mem_store[cid][-5:]

    # El último elemento debe ser del bot
    assert resp["message"][-1]["role"] == "bot"


