def test_health_ok_with_mongo(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mongo"] == "ok"
    assert "version" in body


def test_health_degraded_when_mongo_down(client, repo, monkeypatch):
    monkeypatch.setattr(repo, "ping", lambda: False)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["mongo"] == "unavailable"
