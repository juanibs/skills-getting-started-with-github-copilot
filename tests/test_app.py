import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", copy.deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_root_redirects_to_frontend(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == app_module.activities


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Soccer%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@example.com for Soccer Club"
    }
    assert "student@example.com" in app_module.activities["Soccer Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    signup_url = "/activities/Soccer%20Club/signup"
    params = {"email": "student@example.com"}

    assert client.post(signup_url, params=params).status_code == 200
    response = client.post(signup_url, params=params)

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities["Soccer Club"]["participants"].count(params["email"]) == 1


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email(client):
    response = client.post("/activities/Soccer%20Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant(client):
    activity = app_module.activities["Soccer Club"]
    activity["participants"].append("student@example.com")

    response = client.delete(
        "/activities/Soccer%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered student@example.com from Soccer Club"
    }
    assert "student@example.com" not in activity["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Soccer%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_requires_email(client):
    response = client.delete("/activities/Soccer%20Club/signup")

    assert response.status_code == 422