import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_state = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_state))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_map():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert "Chess Club" in payload
    assert "participants" in payload["Chess Club"]


def test_signup_success_adds_participant():
    email = "newstudent@mergington.edu"
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_unknown_activity_returns_404():
    response = client.post("/activities/Unknown Club/signup", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_participant_returns_400():
    existing_email = app_module.activities["Programming Class"]["participants"][0]
    response = client.post("/activities/Programming Class/signup", params={"email": existing_email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_full_activity_returns_400():
    activity_name = "Debate Team"
    app_module.activities[activity_name]["max_participants"] = len(app_module.activities[activity_name]["participants"])

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is already full"


def test_unregister_success_removes_participant():
    existing_email = app_module.activities["Gym Class"]["participants"][0]
    response = client.delete("/activities/Gym Class/participants", params={"email": existing_email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {existing_email} from Gym Class"
    assert existing_email not in app_module.activities["Gym Class"]["participants"]


def test_unregister_unknown_activity_returns_404():
    response = client.delete("/activities/Unknown Club/participants", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_missing_participant_returns_404():
    missing_email = "missing@mergington.edu"
    response = client.delete("/activities/Drama Club/participants", params={"email": missing_email})

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"
