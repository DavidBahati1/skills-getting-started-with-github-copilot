from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    with TestClient(app) as test_client:
        yield test_client
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"] == {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    }


def test_signup_adds_participant(client):
    email = "new-student@mergington.edu"

    response = client.post("/activities/Drama Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Drama Club"}
    assert email in client.get("/activities").json()["Drama Club"]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "new-student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = "student-to-remove@mergington.edu"
    client.post("/activities/Soccer Team/signup", params={"email": email})

    response = client.delete("/activities/Soccer Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Soccer Team"}
    assert email not in client.get("/activities").json()["Soccer Team"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "detail"),
    [
        ("Unknown Activity", "student@mergington.edu", "Activity not found"),
        ("Soccer Team", "missing-student@mergington.edu", "Participant not found"),
    ],
)
def test_unregister_returns_404_for_unknown_activity_or_participant(
    client, activity_name, email, detail
):
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == detail
