from datetime import date, timedelta

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from authnest.models import User
from tests.constants import PASSWORD
from tests.helpers import client_for, make_image

pytestmark = pytest.mark.django_db

PROFILE = "authnest:profile"
PICTURE = "authnest:profile-picture"

EXPECTED_FIELDS = {
    "id", "email", "phone", "first_name", "last_name", "dob",
    "profile_picture", "is_email_verified", "is_phone_verified", "date_joined",
}


def patch_json(client, data):
    return client.patch(reverse(PROFILE), data, format="json")


def upload(client, image=None):
    return client.patch(
        reverse(PROFILE),
        {"profile_picture": image or make_image()},
        format="multipart",
    )


# ---------- reading the profile ----------

def test_profile_needs_login(api_client):
    assert api_client.get(reverse(PROFILE)).status_code == 401


def test_profile_rejects_a_garbage_bearer_token(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer garbage")
    assert api_client.get(reverse(PROFILE)).status_code == 401


def test_profile_returns_exactly_the_public_fields(auth_client, user):
    data = auth_client.get(reverse(PROFILE)).json()

    assert set(data) == EXPECTED_FIELDS
    assert data["id"] == user.pk
    assert data["email"] == "user@example.com"
    assert data["is_email_verified"] is True
    assert data["profile_picture"] is None


def test_profile_of_a_phone_only_user(db):
    phone_user = User.objects.create_user(phone="+919876543210", password=PASSWORD)

    data = client_for(phone_user).get(reverse(PROFILE)).json()

    assert data["email"] is None
    assert data["phone"] == "+919876543210"


def test_profile_is_blocked_for_a_soft_deleted_user(auth_client, user):
    user.delete()
    assert auth_client.get(reverse(PROFILE)).status_code == 401


# ---------- updating the profile ----------

def test_patch_updates_names_and_dob(auth_client, user):
    response = patch_json(
        auth_client,
        {"first_name": "Ravi", "last_name": "Patel", "dob": "1995-05-20"},
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert (user.first_name, user.last_name) == ("Ravi", "Patel")
    assert user.dob == date(1995, 5, 20)
    assert response.json()["first_name"] == "Ravi"


def test_patch_can_clear_dob(auth_client, user):
    user.dob = date(1995, 5, 20)
    user.save()

    response = patch_json(auth_client, {"dob": None})

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.dob is None


def test_patch_allows_blank_names(auth_client, user):
    user.first_name = "Ravi"
    user.save()
    assert patch_json(auth_client, {"first_name": ""}).status_code == 200
    user.refresh_from_db()
    assert user.first_name == ""


def test_patch_ignores_protected_fields(auth_client, user):
    response = patch_json(
        auth_client,
        {
            "email": "hacker@example.com",
            "phone": "+919999999999",
            "is_staff": True,
            "is_superuser": True,
            "is_email_verified": False,
            "is_phone_verified": True,
        },
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.email == "user@example.com"
    assert user.phone is None
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_email_verified is True
    assert user.is_phone_verified is False


def test_put_is_not_allowed(auth_client):
    response = auth_client.put(
        reverse(PROFILE), {"first_name": "Ravi"}, format="json"
    )
    assert response.status_code == 405


@pytest.mark.parametrize(
    "dob",
    [
        (date.today() + timedelta(days=1)).isoformat(),
        "1800-01-01",
        "not-a-date",
    ],
)
def test_patch_rejects_bad_dob(auth_client, dob):
    response = patch_json(auth_client, {"dob": dob})
    assert response.status_code == 400
    assert "dob" in response.json()


def test_patch_rejects_a_too_long_name(auth_client):
    response = patch_json(auth_client, {"first_name": "a" * 151})
    assert response.status_code == 400
    assert "first_name" in response.json()


# ---------- profile picture ----------

def test_upload_picture_stores_file_and_returns_absolute_url(auth_client, user):
    response = upload(auth_client)

    assert response.status_code == 200
    url = response.json()["profile_picture"]
    assert url.startswith("http://testserver/media/authnest/profiles/")
    user.refresh_from_db()
    assert user.profile_picture.name.startswith("authnest/profiles/")
    assert default_storage.exists(user.profile_picture.name)


def test_non_image_file_is_rejected(auth_client, user):
    fake = SimpleUploadedFile("fake.jpg", b"this is not an image", content_type="image/jpeg")

    response = upload(auth_client, fake)

    assert response.status_code == 400
    assert "profile_picture" in response.json()
    user.refresh_from_db()
    assert not user.profile_picture


def test_too_large_picture_is_rejected(auth_client, user, settings):
    settings.AUTHNEST = {"PROFILE_PICTURE_MAX_SIZE": 10}

    response = upload(auth_client)

    assert response.status_code == 400
    assert "profile_picture" in response.json()
    user.refresh_from_db()
    assert not user.profile_picture


def test_uploading_a_new_picture_removes_the_old_file(auth_client, user):
    upload(auth_client)
    user.refresh_from_db()
    first = user.profile_picture.name

    response = upload(auth_client)
    user.refresh_from_db()
    second = user.profile_picture.name

    assert first != second
    assert not default_storage.exists(first)
    assert default_storage.exists(second)
    assert response.json()["profile_picture"] is not None


def test_updating_names_keeps_the_existing_picture(auth_client, user):
    upload(auth_client)
    user.refresh_from_db()
    name = user.profile_picture.name

    patch_json(auth_client, {"first_name": "Ravi"})

    user.refresh_from_db()
    assert user.profile_picture.name == name
    assert default_storage.exists(name)


def test_sending_null_picture_in_json_removes_it(auth_client, user):
    upload(auth_client)
    user.refresh_from_db()
    name = user.profile_picture.name

    response = patch_json(auth_client, {"profile_picture": None})

    assert response.status_code == 200
    assert response.json()["profile_picture"] is None
    assert not default_storage.exists(name)


def test_delete_picture_endpoint_removes_file_and_field(auth_client, user):
    upload(auth_client)
    user.refresh_from_db()
    name = user.profile_picture.name

    response = auth_client.delete(reverse(PICTURE))

    assert response.status_code == 204
    user.refresh_from_db()
    assert not user.profile_picture
    assert not default_storage.exists(name)
    assert auth_client.get(reverse(PROFILE)).json()["profile_picture"] is None


def test_delete_picture_when_there_is_none_is_still_204(auth_client):
    assert auth_client.delete(reverse(PICTURE)).status_code == 204


def test_delete_picture_needs_login(api_client):
    assert api_client.delete(reverse(PICTURE)).status_code == 401