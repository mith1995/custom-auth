import pytest
from django.urls import reverse

from authnest.models import User
from authnest.services.tokens import (
    make_email_verification_token,
    make_password_reset_token,
)
from tests.constants import PASSWORD
from tests.helpers import extract_token

pytestmark = pytest.mark.django_db


def register(client, **data):
    payload = {"password": PASSWORD, **data}
    return client.post(reverse("authnest:register"), payload, format="json")


def verify(client, token):
    return client.post(reverse("authnest:verify-email"), {"token": token}, format="json")


def resend(client, email):
    return client.post(
        reverse("authnest:resend-verification"), {"email": email}, format="json"
    )


# ---------- register ----------

def test_register_with_email_creates_user_and_sends_mail(api_client, mailoutbox):
    response = register(api_client, email="new@example.com")

    assert response.status_code == 201
    user = User.objects.get(email="new@example.com")
    assert user.is_email_verified is False
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["new@example.com"]


def test_register_response_never_contains_password(api_client):
    response = register(api_client, email="new@example.com")
    assert "password" not in response.json()["user"]
    assert response.json()["user"]["email"] == "new@example.com"


def test_register_stores_email_in_lowercase(api_client):
    register(api_client, email="NEW@Example.com")
    assert User.objects.filter(email="new@example.com").exists()


def test_register_is_open_even_with_a_bad_authorization_header(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer garbage")
    assert register(api_client, email="new@example.com").status_code == 201


def test_register_duplicate_email_is_rejected_case_insensitively(api_client, user):
    response = register(api_client, email="USER@example.com")
    assert response.status_code == 400
    assert "email" in response.json()


def test_register_rejects_email_of_soft_deleted_user(api_client, user):
    user.delete()
    response = register(api_client, email="user@example.com")
    assert response.status_code == 400
    assert "email" in response.json()


@pytest.mark.parametrize("password", ["12345678", "short"])
def test_register_rejects_weak_password(api_client, password):
    response = register(api_client, email="new@example.com", password=password)
    assert response.status_code == 400
    assert "password" in response.json()
    assert not User.objects.filter(email="new@example.com").exists()


def test_register_rejects_password_similar_to_email(api_client):
    response = register(
        api_client, email="ravipatel@example.com", password="ravipatel"
    )
    assert response.status_code == 400
    assert "password" in response.json()


def test_register_needs_an_identifier(api_client):
    assert register(api_client).status_code == 400


def test_register_rejects_phone_when_phone_login_is_off(api_client):
    response = register(api_client, phone="+919876543210")
    assert response.status_code == 400
    assert "phone" in response.json()


def test_phone_only_registration_sends_no_email(api_client, settings, mailoutbox):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["email", "phone"]}
    response = register(api_client, phone="+919876543210")

    assert response.status_code == 201
    assert User.objects.filter(phone="+919876543210").exists()
    assert len(mailoutbox) == 0


def test_register_rejects_badly_formatted_phone(api_client, settings):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["email", "phone"]}
    response = register(api_client, phone="9876543210")
    assert response.status_code == 400
    assert "phone" in response.json()


def test_phone_is_required_when_phone_is_the_only_method(api_client, settings):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["phone"]}
    assert register(api_client, email="new@example.com").status_code == 400
    assert register(api_client, phone="+919876543210").status_code == 201


def test_no_verification_mail_when_verification_is_off(api_client, settings, mailoutbox):
    settings.AUTHNEST = {"REQUIRE_EMAIL_VERIFICATION": False}
    assert register(api_client, email="new@example.com").status_code == 201
    assert len(mailoutbox) == 0


def test_register_succeeds_even_if_email_sending_fails(api_client, monkeypatch):
    def boom(user):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("authnest.serializers.send_verification_email", boom)

    response = register(api_client, email="new@example.com")
    assert response.status_code == 201
    assert User.objects.filter(email="new@example.com").exists()


# ---------- verify email ----------

def test_full_flow_register_then_verify_with_token_from_mail(api_client, mailoutbox):
    register(api_client, email="new@example.com")
    token = extract_token(mailoutbox[0])

    response = verify(api_client, token)

    assert response.status_code == 200
    assert User.objects.get(email="new@example.com").is_email_verified is True


def test_verifying_twice_is_fine(api_client):
    user = User.objects.create_user(email="a@example.com", password=PASSWORD)
    token = make_email_verification_token(user)
    assert verify(api_client, token).status_code == 200
    assert verify(api_client, token).status_code == 200


@pytest.mark.parametrize("token", ["", "garbage", "abc:def:ghi"])
def test_verify_rejects_bad_token(api_client, token):
    response = verify(api_client, token)
    assert response.status_code == 400
    assert "token" in response.json()


def test_verify_rejects_expired_token(api_client, settings):
    user = User.objects.create_user(email="a@example.com", password=PASSWORD)
    token = make_email_verification_token(user)
    settings.AUTHNEST = {"EMAIL_VERIFIFCATION_TIMEOUT": -1}  # har token expire maana jayega

    assert verify(api_client, token).status_code == 400
    user.refresh_from_db()
    assert user.is_email_verified is False


def test_verify_rejects_token_after_email_changed(api_client):
    user = User.objects.create_user(email="a@example.com", password=PASSWORD)
    token = make_email_verification_token(user)
    user.email = "changed@example.com"
    user.save()

    assert verify(api_client, token).status_code == 400


def test_verify_rejects_token_of_another_purpose(api_client):
    user = User.objects.create_user(email="a@example.com", password=PASSWORD)
    reset_token = make_password_reset_token(user)

    assert verify(api_client, reset_token).status_code == 400


def test_verify_rejects_token_of_soft_deleted_user(api_client):
    user = User.objects.create_user(email="a@example.com", password=PASSWORD)
    token = make_email_verification_token(user)
    user.delete()

    assert verify(api_client, token).status_code == 400


# ---------- resend verification ----------

def test_resend_sends_mail_to_unverified_user(api_client, mailoutbox):
    User.objects.create_user(email="a@example.com", password=PASSWORD)

    response = resend(api_client, "a@example.com")

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["a@example.com"]


def test_resend_does_not_mail_a_verified_user(api_client, user, mailoutbox):
    assert resend(api_client, user.email).status_code == 200
    assert len(mailoutbox) == 0


def test_resend_does_not_mail_a_soft_deleted_user(api_client, mailoutbox):
    user = User.objects.create_user(email="a@example.com", password=PASSWORD)
    user.delete()

    assert resend(api_client, "a@example.com").status_code == 200
    assert len(mailoutbox) == 0


def test_resend_response_is_identical_for_known_and_unknown_email(api_client):
    User.objects.create_user(email="a@example.com", password=PASSWORD)

    known = resend(api_client, "a@example.com")
    unknown = resend(api_client, "nobody@example.com")

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


def test_resend_rejects_invalid_email_format(api_client):
    assert resend(api_client, "not-an-email").status_code == 400