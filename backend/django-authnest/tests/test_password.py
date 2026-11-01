import pytest
from django.urls import reverse
from rest_framework_simplejwt.exceptions import TokenError

from authnest.models import User
from authnest.services.tokens import (
    AuthnestRefreshToken,
    issue_tokens,
    make_email_verification_token,
    make_password_reset_token,
    read_password_reset_token,
)
from tests.constants import NEW_PASSWORD, PASSWORD
from tests.helpers import extract_token

pytestmark = pytest.mark.django_db

COOKIE = "authnest_refresh"


def forgot(client, email):
    return client.post(reverse("authnest:forgot-password"), {"email": email}, format="json")


def reset(client, token, password):
    return client.post(
        reverse("authnest:reset-password"),
        {"token": token, "password": password},
        format="json",
    )


def change(client, old, new):
    return client.post(
        reverse("authnest:change-password"),
        {"old_password": old, "new_password": new},
        format="json",
    )


def login(client, identifier, password):
    return client.post(
        reverse("authnest:login"),
        {"identifier": identifier, "password": password},
        format="json",
    )


def is_blacklisted(refresh_token):
    with pytest.raises(TokenError):
        AuthnestRefreshToken(refresh_token)


# ---------- forgot password ----------

def test_forgot_sends_reset_mail_with_a_valid_token(api_client, user, mailoutbox):
    response = forgot(api_client, "user@example.com")

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["user@example.com"]
    payload = read_password_reset_token(extract_token(mailoutbox[0]))
    assert payload["uid"] == user.pk


def test_forgot_matches_email_case_insensitively(api_client, user, mailoutbox):
    assert forgot(api_client, "USER@Example.com").status_code == 200
    assert len(mailoutbox) == 1


def test_forgot_response_is_identical_for_known_and_unknown_email(api_client, user):
    known = forgot(api_client, "user@example.com")
    unknown = forgot(api_client, "nobody@example.com")

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


def test_forgot_sends_nothing_to_an_unknown_email(api_client, user, mailoutbox):
    forgot(api_client, "nobody@example.com")
    assert len(mailoutbox) == 0


def test_forgot_sends_nothing_to_a_soft_deleted_user(api_client, user, mailoutbox):
    user.delete()
    assert forgot(api_client, "user@example.com").status_code == 200
    assert len(mailoutbox) == 0


def test_forgot_sends_nothing_to_an_inactive_user(api_client, user, mailoutbox):
    user.is_active = False
    user.save()
    assert forgot(api_client, "user@example.com").status_code == 200
    assert len(mailoutbox) == 0


def test_forgot_rejects_invalid_email_format(api_client):
    assert forgot(api_client, "not-an-email").status_code == 400


def test_forgot_is_still_200_if_email_sending_fails(api_client, user, monkeypatch):
    def boom(user):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("authnest.views.send_password_reset_email", boom)

    assert forgot(api_client, "user@example.com").status_code == 200


# ---------- reset password ----------

def test_full_flow_forgot_then_reset_then_login(api_client, user, mailoutbox):
    forgot(api_client, "user@example.com")
    token = extract_token(mailoutbox[0])

    response = reset(api_client, token, NEW_PASSWORD)

    assert response.status_code == 200
    assert login(api_client, "user@example.com", NEW_PASSWORD).status_code == 200
    assert login(api_client, "user@example.com", PASSWORD).status_code == 401


def test_reset_sends_password_changed_notice(api_client, user, mailoutbox):
    token = make_password_reset_token(user)

    reset(api_client, token, NEW_PASSWORD)

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["user@example.com"]
    assert mailoutbox[0].subject == "Your password has been changed successfully."


def test_reset_does_not_log_the_user_in(api_client, user):
    token = make_password_reset_token(user)

    response = reset(api_client, token, NEW_PASSWORD)

    assert "access" not in response.json()
    assert COOKIE not in response.cookies


def test_reset_link_works_only_once(api_client, user):
    token = make_password_reset_token(user)

    assert reset(api_client, token, NEW_PASSWORD).status_code == 200
    assert reset(api_client, token, "Third-Str0ng-Pass-789").status_code == 400
    assert login(api_client, "user@example.com", NEW_PASSWORD).status_code == 200


def test_weak_password_is_rejected_and_the_link_stays_usable(api_client, user):
    token = make_password_reset_token(user)

    weak = reset(api_client, token, "12345678")

    assert weak.status_code == 400
    assert "password" in weak.json()
    user.refresh_from_db()
    assert user.check_password(PASSWORD)
    assert reset(api_client, token, NEW_PASSWORD).status_code == 200


@pytest.mark.parametrize("token", ["", "garbage", "abc:def:ghi"])
def test_reset_rejects_bad_token(api_client, user, token):
    response = reset(api_client, token, NEW_PASSWORD)
    assert response.status_code == 400
    assert "token" in response.json()


def test_reset_rejects_expired_token(api_client, user, settings):
    token = make_password_reset_token(user)
    settings.AUTHNEST = {"PASSWORD_RESET_TIMEOUT": -1}

    assert reset(api_client, token, NEW_PASSWORD).status_code == 400
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_reset_rejects_a_token_made_for_another_purpose(api_client, user):
    token = make_email_verification_token(user)
    assert reset(api_client, token, NEW_PASSWORD).status_code == 400


def test_reset_token_dies_when_the_password_changes_elsewhere(api_client, user):
    token = make_password_reset_token(user)
    user.set_password("Changed-Str0ng-Pass-321")
    user.save()

    assert reset(api_client, token, NEW_PASSWORD).status_code == 400


def test_reset_rejects_token_of_soft_deleted_user(api_client, user):
    token = make_password_reset_token(user)
    user.delete()
    assert reset(api_client, token, NEW_PASSWORD).status_code == 400


def test_reset_rejects_token_of_inactive_user(api_client, user):
    token = make_password_reset_token(user)
    user.is_active = False
    user.save()
    assert reset(api_client, token, NEW_PASSWORD).status_code == 400


@pytest.mark.parametrize(
    "body", [{}, {"token": "x"}, {"password": NEW_PASSWORD}]
)
def test_reset_needs_token_and_password(api_client, body):
    response = api_client.post(reverse("authnest:reset-password"), body, format="json")
    assert response.status_code == 400


def test_reset_blacklists_every_refresh_token_of_the_user(api_client, user):
    first = issue_tokens(user)
    second = issue_tokens(user)
    token = make_password_reset_token(user)

    reset(api_client, token, NEW_PASSWORD)

    is_blacklisted(first["refresh"])
    is_blacklisted(second["refresh"])


def test_refresh_cookie_stops_working_after_reset(api_client, user):
    login(api_client, "user@example.com", PASSWORD)
    token = make_password_reset_token(user)

    reset(api_client, token, NEW_PASSWORD)

    assert api_client.post(reverse("authnest:token-refresh")).status_code == 401


def test_reset_works_for_a_phone_only_user_and_sends_no_mail(api_client, mailoutbox):
    phone_user = User.objects.create_user(phone="+919876543210", password=PASSWORD)
    token = make_password_reset_token(phone_user)

    assert reset(api_client, token, NEW_PASSWORD).status_code == 200
    assert len(mailoutbox) == 0
    phone_user.refresh_from_db()
    assert phone_user.check_password(NEW_PASSWORD)


def test_reset_is_atomic_password_is_not_changed_if_blacklisting_fails(
    api_client, user, monkeypatch
):
    def boom(user):
        raise RuntimeError("blacklist failed")

    monkeypatch.setattr("authnest.views.blacklist_all_tokens", boom)
    token = make_password_reset_token(user)

    with pytest.raises(RuntimeError):
        reset(api_client, token, NEW_PASSWORD)

    user.refresh_from_db()
    assert user.check_password(PASSWORD)


# ---------- change password ----------

def test_change_password_needs_login(api_client):
    assert change(api_client, PASSWORD, NEW_PASSWORD).status_code == 401


def test_change_password_rejects_a_garbage_bearer_token(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer garbage")
    assert change(api_client, PASSWORD, NEW_PASSWORD).status_code == 401


def test_change_password_success(auth_client, user, mailoutbox):
    response = change(auth_client, PASSWORD, NEW_PASSWORD)

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert not user.check_password(PASSWORD)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Your password has been changed successfully."


def test_change_password_rejects_wrong_old_password(auth_client, user):
    response = change(auth_client, "galat-purana", NEW_PASSWORD)

    assert response.status_code == 400
    assert "old_password" in response.json()
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_change_password_rejects_same_new_password(auth_client):
    response = change(auth_client, PASSWORD, PASSWORD)
    assert response.status_code == 400
    assert "new_password" in response.json()


def test_change_password_rejects_weak_new_password(auth_client, user):
    response = change(auth_client, PASSWORD, "12345678")

    assert response.status_code == 400
    assert "new_password" in response.json()
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


@pytest.mark.parametrize(
    "body", [{}, {"old_password": PASSWORD}, {"new_password": NEW_PASSWORD}]
)
def test_change_password_needs_both_fields(auth_client, body):
    response = auth_client.post(reverse("authnest:change-password"), body, format="json")
    assert response.status_code == 400


def test_change_password_blacklists_every_refresh_token(auth_client, user):
    first = issue_tokens(user)
    second = issue_tokens(user)

    change(auth_client, PASSWORD, NEW_PASSWORD)

    is_blacklisted(first["refresh"])
    is_blacklisted(second["refresh"])


def test_change_password_clears_the_refresh_cookie_in_cookie_mode(api_client, user):
    access = login(api_client, "user@example.com", PASSWORD).json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = change(api_client, PASSWORD, NEW_PASSWORD)

    assert response.cookies[COOKIE]["max-age"] == 0
    assert api_client.post(reverse("authnest:token-refresh")).status_code == 401


def test_change_password_in_body_mode_touches_no_cookie(auth_client, settings):
    settings.AUTHNEST = {"REFRESH_TOKEN_IN_COOKIE": False}

    response = change(auth_client, PASSWORD, NEW_PASSWORD)

    assert response.status_code == 200
    assert COOKIE not in response.cookies


def test_old_access_token_still_works_until_it_expires(auth_client):
    # Known design limit: access tokens blacklist nahi hote, isliye ACCESS_TOKEN_LIFETIME chhota rakhte hain.
    change(auth_client, PASSWORD, NEW_PASSWORD)
    assert auth_client.get(reverse("authnest:profile")).status_code == 200


def test_soft_deleted_user_cannot_change_password(auth_client, user):
    user.delete()
    assert change(auth_client, PASSWORD, NEW_PASSWORD).status_code == 401