from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_page():
    response = client.get("/")

    assert response.status_code == 200
    assert "ComicCraft" in response.text


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_validation():
    response = client.post(
        "/generate-comic/json",
        json={
            "prompt": "",
            "character_name": "Ravi",
            "setting": "A small Indian town",
            "tone": "Inspirational",
            "art_style": "2D cartoon style",
        },
    )

    assert response.status_code == 422