from fastapi.testclient import TestClient

import api.routes.profile as profile_routes
import api.routes.subjects as subject_routes
from app.main import app


client = TestClient(app)


PROFILE = {
    "first_name": "Jan",
    "last_name": "Kowalski",
    "university": "Politechnika Lubelska",
    "faculty": "WEiI",
    "field_of_study": "Informatyka",
    "semester": "4",
    "group": "1",
    "academic_year": "2025/2026",
}


SUBJECT = {
    "id": "subject-1",
    "name": "Maszyny elektryczne",
    "instructor_name": "Jan Nowak",
    "department": "Katedra Elektrotechniki",
    "laboratory": "Lab 1",
}


def test_health():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
    }


def test_get_profile(
    monkeypatch,
):
    monkeypatch.setattr(
        profile_routes,
        "load_user_profile",
        lambda: PROFILE,
    )

    response = client.get(
        "/profile"
    )

    assert response.status_code == 200
    assert response.json() == PROFILE


def test_get_profile_returns_404_when_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        profile_routes,
        "load_user_profile",
        lambda: None,
    )

    response = client.get(
        "/profile"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "User profile not found.",
    }


def test_put_profile(
    monkeypatch,
):
    captured = {}

    def fake_save(profile):
        captured["profile"] = profile
        return profile

    monkeypatch.setattr(
        profile_routes,
        "save_user_profile",
        fake_save,
    )

    response = client.put(
        "/profile",
        json=PROFILE,
    )

    assert response.status_code == 200
    assert response.json() == PROFILE

    saved_profile = captured[
        "profile"
    ]

    assert (
        saved_profile.first_name
        == "Jan"
    )

    assert (
        saved_profile.last_name
        == "Kowalski"
    )


def test_patch_profile(
    monkeypatch,
):
    def fake_update(update):
        result = PROFILE.copy()

        if update.first_name is not None:
            result["first_name"] = (
                update.first_name
            )

        return result

    monkeypatch.setattr(
        profile_routes,
        "update_user_profile",
        fake_update,
    )

    response = client.patch(
        "/profile",
        json={
            "first_name": "Adam",
        },
    )

    assert response.status_code == 200

    assert response.json()[
        "first_name"
    ] == "Adam"


def test_patch_missing_profile_returns_404(
    monkeypatch,
):
    def fake_update(update):
        raise ValueError(
            "User profile not found."
        )

    monkeypatch.setattr(
        profile_routes,
        "update_user_profile",
        fake_update,
    )

    response = client.patch(
        "/profile",
        json={
            "first_name": "Adam",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "User profile not found.",
    }


def test_profile_validation_error():
    response = client.put(
        "/profile",
        json={
            "first_name": "Jan",
        },
    )

    assert response.status_code == 422


def test_get_subjects(
    monkeypatch,
):
    monkeypatch.setattr(
        subject_routes,
        "load_subjects",
        lambda: [SUBJECT],
    )

    response = client.get(
        "/subjects"
    )

    assert response.status_code == 200

    assert response.json() == [
        SUBJECT
    ]


def test_get_single_subject(
    monkeypatch,
):
    def fake_get_subject(
        subject_id,
    ):
        assert subject_id == "subject-1"
        return SUBJECT

    monkeypatch.setattr(
        subject_routes,
        "get_subject",
        fake_get_subject,
    )

    response = client.get(
        "/subjects/subject-1"
    )

    assert response.status_code == 200
    assert response.json() == SUBJECT


def test_get_unknown_subject_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        subject_routes,
        "get_subject",
        lambda subject_id: None,
    )

    response = client.get(
        "/subjects/unknown"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Subject not found.",
    }


def test_create_subject(
    monkeypatch,
):
    captured = {}

    def fake_create(data):
        captured["data"] = data

        return {
            "id": "subject-1",
            "name": data.name,
            "instructor_name": (
                data.instructor_name
            ),
            "department": (
                data.department
            ),
            "laboratory": (
                data.laboratory
            ),
        }

    monkeypatch.setattr(
        subject_routes,
        "create_subject",
        fake_create,
    )

    response = client.post(
        "/subjects",
        json={
            "name": (
                "Maszyny elektryczne"
            ),
            "instructor_name": (
                "Jan Nowak"
            ),
            "department": (
                "Katedra Elektrotechniki"
            ),
            "laboratory": "Lab 1",
        },
    )

    assert response.status_code == 201
    assert response.json() == SUBJECT

    assert (
        captured["data"].name
        == "Maszyny elektryczne"
    )


def test_create_subject_validation_error():
    response = client.post(
        "/subjects",
        json={
            "name": (
                "Maszyny elektryczne"
            ),
        },
    )

    assert response.status_code == 422


def test_patch_subject(
    monkeypatch,
):
    def fake_update(
        subject_id,
        update,
    ):
        assert subject_id == (
            "subject-1"
        )

        result = SUBJECT.copy()

        if update.name is not None:
            result["name"] = (
                update.name
            )

        return result

    monkeypatch.setattr(
        subject_routes,
        "update_subject",
        fake_update,
    )

    response = client.patch(
        "/subjects/subject-1",
        json={
            "name": (
                "Nowa nazwa przedmiotu"
            ),
        },
    )

    assert response.status_code == 200

    assert response.json()[
        "name"
    ] == "Nowa nazwa przedmiotu"


def test_patch_unknown_subject_returns_404(
    monkeypatch,
):
    def fake_update(
        subject_id,
        update,
    ):
        raise ValueError(
            "Subject not found."
        )

    monkeypatch.setattr(
        subject_routes,
        "update_subject",
        fake_update,
    )

    response = client.patch(
        "/subjects/unknown",
        json={
            "name": "Test",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Subject not found.",
    }


def test_delete_subject(
    monkeypatch,
):
    captured = {}

    def fake_delete(
        subject_id,
    ):
        captured["subject_id"] = (
            subject_id
        )

    monkeypatch.setattr(
        subject_routes,
        "delete_subject",
        fake_delete,
    )

    response = client.delete(
        "/subjects/subject-1"
    )

    assert response.status_code == 204
    assert response.content == b""

    assert (
        captured["subject_id"]
        == "subject-1"
    )


def test_delete_unknown_subject_returns_404(
    monkeypatch,
):
    def fake_delete(
        subject_id,
    ):
        raise ValueError(
            "Subject not found."
        )

    monkeypatch.setattr(
        subject_routes,
        "delete_subject",
        fake_delete,
    )

    response = client.delete(
        "/subjects/unknown"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Subject not found.",
    }