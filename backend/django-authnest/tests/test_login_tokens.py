import pytest
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import AccessToken

from authnest.models import User
from authnest.services.tokens import AuthnestRefreshToken
from tests.constants import PASSWORD

pytestmark = pytest.mark.django_db

COOKIE = "authnest_refresh"


def login(client, identifier="user@example.com", password=PASSWORD, url="authnest:login"):
    return client.post(
        reverse(url), {"identifier": identifier, "password": password}, format="json"
    )


def admin_login(client, identifier="admin", password=PASSWORD):
    return login(client, identifier, password, url="authnest:admin-login")


def refresh(client, **body):
    return client.post(reverse("authnest:token-refresh"), body, format="json")


def logout(client, **body):
    return client.post(reverse("authnest:logout"), body, format="json")


def refresh_cookie(client, name=COOKIE):
    return client.cookies[name].value


# ---------- login ----------

def test_login_returns_access_token_and_user_but_no_refresh_in_body(api_client, user):
    response = login(api_client)
    data = response.json()

    assert response.status_code == 200
    assert data["access"]
    assert "refresh" not in data
    assert data["user"]["email"] == "user@example.com"
    assert "password" not in data["user"]


def test_login_sets_httponly_refresh_cookie(api_client, user):
    response = login(api_client)
    cookie = response.cookies[COOKIE]

    assert cookie.value
    assert cookie["httponly"]
    assert cookie["samesite"] == "Lax"
    assert cookie["path"] == "/"
    assert cookie["max-age"] == 7 * 24 * 3600


def test_login_updates_last_login(api_client, user):
    assert user.last_login is None
    login(api_client)
    user.refresh_from_db()
    assert user.last_login is not None


def test_login_ignores_case_and_spaces_in_email(api_client, user):
    assert login(api_client, "  USER@Example.COM ").status_code == 200


def test_wrong_password_and_unknown_user_look_identical(api_client, user):
    wrong_password = login(api_client, password="galat")
    unknown_user = login(api_client, identifier="koi@nahi.com")

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()
    assert wrong_password.json()["code"] == "invalid_credentials"


def test_failed_login_sets_no_cookie(api_client, user):
    response = login(api_client, password="galat")
    assert COOKIE not in response.cookies


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"identifier": "user@example.com"},
        {"password": PASSWORD},
        {"identifier": "", "password": PASSWORD},
    ],
)
def test_login_needs_identifier_and_password(api_client, user, body):
    response = api_client.post(reverse("authnest:login"), body, format="json")
    assert response.status_code == 400


def test_phone_login_is_off_by_default(api_client):
    User.objects.create_user(phone="+919876543210", password=PASSWORD)
    assert login(api_client, "+919876543210").status_code == 401


def test_phone_login_works_when_enabled(api_client, settings):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["email", "phone"]}
    User.objects.create_user(phone="+919876543210", password=PASSWORD)
    assert login(api_client, "+91 98765 43210").status_code == 200


def test_phone_only_user_needs_no_email_verification(api_client, settings):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["phone"]}
    User.objects.create_user(phone="+919876543210", password=PASSWORD)
    assert login(api_client, "+919876543210").status_code == 200


def test_unverified_email_blocks_login_with_clear_code(api_client):
    User.objects.create_user(email="new@example.com", password=PASSWORD)

    response = login(api_client, "new@example.com")

    assert response.status_code == 403
    assert response.json()["code"] == "email_not_verified"
    assert COOKIE not in response.cookies


def test_wrong_password_on_unverified_user_is_401_not_403(api_client):
    User.objects.create_user(email="new@example.com", password=PASSWORD)
    assert login(api_client, "new@example.com", password="galat").status_code == 401


def test_unverified_user_can_login_when_verification_is_off(api_client, settings):
    settings.AUTHNEST = {"REQUIRE_EMAIL_VERIFICATION": False}
    User.objects.create_user(email="new@example.com", password=PASSWORD)
    assert login(api_client, "new@example.com").status_code == 200


def test_inactive_user_cannot_login(api_client, user):
    user.is_active = False
    user.save()
    assert login(api_client).status_code == 401


def test_soft_deleted_user_cannot_login_until_restored(api_client, user):
    user.delete()
    assert login(api_client).status_code == 401

    User.all_objects.filter(pk=user.pk).restore()
    assert login(api_client).status_code == 200


# ---------- user and admin scopes ----------

def test_admin_login_with_username(api_client, admin_user):
    response = admin_login(api_client)

    assert response.status_code == 200
    assert response.json()["user"]["is_staff"] is True


def test_admin_cannot_use_the_user_login_endpoint(api_client, admin_user):
    assert login(api_client, "admin@example.com").status_code == 401
    assert login(api_client, "admin").status_code == 401


def test_normal_user_cannot_use_the_admin_login_endpoint(api_client, user):
    assert admin_login(api_client, "user@example.com").status_code == 401


def test_admin_email_login_works_when_enabled(api_client, admin_user, settings):
    settings.AUTHNEST = {"ADMIN_LOGIN_METHODS": ["username", "email"]}
    assert admin_login(api_client, "admin@example.com").status_code == 200


# ---------- tokens and cookie settings ----------

def test_token_lifetimes_follow_settings(api_client, user, settings):
    settings.AUTHNEST = {"ACCESS_TOKEN_LIFETIME": 60, "REFRESH_TOKEN_LIFETIME": 3600}

    response = login(api_client)
    access = AccessToken(response.json()["access"])
    refresh_token = AuthnestRefreshToken(refresh_cookie(api_client))

    assert abs((access["exp"] - access["iat"]) - 60) <= 1
    assert refresh_token["exp"] - refresh_token["iat"] == 3600
    assert response.cookies[COOKIE]["max-age"] == 3600


@pytest.mark.parametrize("debug, expect_secure", [(True, False), (False, True)])
def test_cookie_secure_flag_in_auto_mode_follows_debug(
    api_client, user, settings, debug, expect_secure
):
    settings.AUTHNEST = {"REFRESH_COOKIE_SECURE": None}
    settings.DEBUG = debug

    response = login(api_client)

    assert bool(response.cookies[COOKIE]["secure"]) is expect_secure


def test_cookie_name_and_samesite_are_configurable(api_client, user, settings):
    settings.AUTHNEST = {
        "REFRESH_COOKIE_NAME": "my_refresh",
        "REFRESH_COOKIE_SAMESITE": "Strict",
    }

    response = login(api_client)

    assert "my_refresh" in response.cookies
    assert COOKIE not in response.cookies
    assert response.cookies["my_refresh"]["samesite"] == "Strict"
    assert refresh(api_client).status_code == 200


def test_body_mode_returns_refresh_in_body_and_sets_no_cookie(api_client, user, settings):
    settings.AUTHNEST = {"REFRESH_TOKEN_IN_COOKIE": False}

    response = login(api_client)

    assert response.json()["refresh"]
    assert COOKIE not in response.cookies


def test_access_token_works_on_a_protected_endpoint(api_client, user):
    access = login(api_client).json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = api_client.get(reverse("authnest:profile"))

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


# ---------- refresh ----------

def test_refresh_returns_new_access_and_rotates_the_cookie(api_client, user):
    login(api_client)
    old = refresh_cookie(api_client)

    response = refresh(api_client)

    assert response.status_code == 200
    assert response.json()["access"]
    assert "refresh" not in response.json()
    assert refresh_cookie(api_client) != old


def test_old_refresh_token_is_rejected_after_rotation(api_client, user):
    login(api_client)
    old = refresh_cookie(api_client)
    refresh(api_client)

    api_client.cookies[COOKIE] = old

    assert refresh(api_client).status_code == 401


def test_refresh_without_cookie_is_401_and_clears_cookie(api_client):
    response = refresh(api_client)

    assert response.status_code == 401
    assert response.json()["code"] == "token_invalid"
    assert response.cookies[COOKIE]["max-age"] == 0


def test_refresh_with_garbage_token_is_401(api_client):
    api_client.cookies[COOKIE] = "garbage"
    assert refresh(api_client).status_code == 401


def test_access_token_cannot_be_used_as_refresh_token(api_client, user):
    access = login(api_client).json()["access"]
    api_client.cookies[COOKIE] = access
    assert refresh(api_client).status_code == 401


def test_refresh_in_body_mode_rotates_too(api_client, user, settings):
    settings.AUTHNEST = {"REFRESH_TOKEN_IN_COOKIE": False}
    first = login(api_client).json()["refresh"]

    response = refresh(api_client, refresh=first)

    assert response.status_code == 200
    assert response.json()["refresh"] != first
    assert COOKIE not in response.cookies
    assert refresh(api_client, refresh=first).status_code == 401


def test_refresh_without_rotation_keeps_the_same_token(api_client, user, settings):
    settings.AUTHNEST = {"REFRESH_TOKEN_ROTATION": False}
    login(api_client)
    old = refresh_cookie(api_client)

    assert refresh(api_client).status_code == 200
    assert refresh_cookie(api_client) == old
    assert refresh(api_client).status_code == 200


def test_refresh_is_blocked_for_a_soft_deleted_user(api_client, user):
    login(api_client)
    user.delete()
    assert refresh(api_client).status_code == 401


def test_refresh_is_blocked_for_an_inactive_user(api_client, user):
    login(api_client)
    user.is_active = False
    user.save()
    assert refresh(api_client).status_code == 401


def test_rotation_records_tokens_in_blacklist_tables(api_client, user):
    login(api_client)
    assert OutstandingToken.objects.filter(user=user).count() == 1
    assert BlacklistedToken.objects.filter(token__user=user).count() == 0

    refresh(api_client)

    assert OutstandingToken.objects.filter(user=user).count() == 2
    assert BlacklistedToken.objects.filter(token__user=user).count() == 1


# ---------- logout ----------

def test_logout_blacklists_the_token_and_clears_the_cookie(api_client, user):
    login(api_client)
    old = refresh_cookie(api_client)

    response = logout(api_client)

    assert response.status_code == 200
    assert refresh_cookie(api_client) == ""
    assert BlacklistedToken.objects.filter(token__user=user).count() == 1

    api_client.cookies[COOKIE] = old
    assert refresh(api_client).status_code == 401


def test_logout_without_a_token_is_still_200(api_client):
    assert logout(api_client).status_code == 200


def test_logout_with_a_garbage_token_is_still_200(api_client):
    api_client.cookies[COOKIE] = "garbage"
    assert logout(api_client).status_code == 200


def test_logout_in_body_mode(api_client, user, settings):
    settings.AUTHNEST = {"REFRESH_TOKEN_IN_COOKIE": False}
    token = login(api_client).json()["refresh"]

    response = logout(api_client, refresh=token)

    assert response.status_code == 200
    assert COOKIE not in response.cookies
    assert refresh(api_client, refresh=token).status_code == 401