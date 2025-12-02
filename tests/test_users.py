from datetime import date

import pytest

from models import SexualOrientation, Interest, Profile, ProfileImage
import models


def test_get_merge_info(client, db_session):
    # seed two orientations and two interests
    o1 = SexualOrientation(orientation_name="Straight")
    o2 = SexualOrientation(orientation_name="Gay")
    i1 = Interest(interest_name="Hiking")
    i2 = Interest(interest_name="Reading")

    db_session.add_all([o1, o2, i1, i2])
    db_session.commit()

    resp = client.get("/user/complete_profile")
    assert resp.status_code == 200
    body = resp.json()
    assert "sexual_orientations" in body
    assert "interests" in body
    assert len(body["sexual_orientations"]) == 2
    assert len(body["interests"]) == 2


def test_create_profile(client, db_session):
    # seed a sexual orientation and an interest
    so = SexualOrientation(orientation_name="Bisexual")
    db_session.add(so)
    db_session.commit()

    interest = Interest(interest_name="Cooking")
    db_session.add(interest)
    db_session.commit()

    payload = {
        "username": "alice",
        "introduction": "Hello, I'm Alice",
        "birthday": "1995-01-01",
        "sexual_orientation_id": so.id,
        "interest_ids": [interest.id],
        "image_urls": ["http://example.com/a.jpg"]
    }

    resp = client.post("/user/complete_profile?user_id=1", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_id"] == 1
    assert data["user_id"] == 1

    # Verify DB state
    profile = db_session.query(models.Profile).filter_by(id=1).first()
    assert profile is not None
    assert profile.username == "alice"
    # image created?
    assert len(profile.images) == 1
    assert profile.images[0].image_url == "http://example.com/a.jpg"
    # interest associated?
    assert len(profile.interests) == 1
    assert profile.interests[0].interest_name == "Cooking"
