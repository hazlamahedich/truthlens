from fastapi.testclient import TestClient

from .query import app

client = TestClient(app)


def test_handle_query():
    query_text = "test query"
    response = client.post("/api/query", json={"queryText": query_text})

    assert response.status_code == 200
    data = response.json()

    assert "format" in data
    assert "content" in data
    assert "sources" in data

    assert data["format"] == "debate"
    assert (
        data["content"]["statement"]
        == "This is a mocked summary for the query: " + query_text
    )
    assert isinstance(data["content"]["for"], list)
    assert isinstance(data["content"]["against"], list)
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) == 2
    assert data["sources"][0]["title"] == "Mocked Source 1"
