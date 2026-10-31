import pytest
from django.urls import reverse
from rest_framework_simplejwt.exceptions import TokenError

from authnest.models import User
from authnest.services.tokens import (
    AuthnestRefreshToken,
    issue_tokens,
    make_email_change_token,
    make_password_reset_token,
    read_email_change_token,
)
from tests.constants import NEW_PASSWORD, PASSWORD
from tests.helpers import client_for, extract_token

pytestmark = pytest.mark.django_db

COOKIE = "authnest_refresh"


def request_change(client, new_email, password=PASSWORD):
    return client.post(
        reverse("authnest:email-change"),
        {"new_email": new_email, "password": password},
        format="json",
    )


def confirm(client, token):
    return client.post(
        reverse("authnest:email-change-confirm"), {"token": token}, format="json"
    )


def delete_account(client, password=PASSWORD):
    return client.post(
        reverse("authnest:account-delete"), {"password": password}, format="json"
    )


def login(client, identifier, password=PASSWORD):
    return client.post(
        reverse("authnest:login"),
        {"identifier": identifier, "password": password},
        format="json",
    )


def assert_blacklisted(refresh_token):
    with pytest.raises(TokenError):
        AuthnestRefreshToken(refresh_token)


# ======================= email change: request =======================

def test_email_change_needs_login(api_client):
    assert request_change(api_client, "new@example.com").status_code == 401


def test_email_change_request_mails_the_new_address_only(auth_client, user, mailoutbox):
    response = request_change(auth_client, "new@example.com")

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["new@example.com"]
    assert "/confirm-email-change" in mailoutbox[0].body
    user.refresh_from_db()
    assert user.email == "user@example.com"  # abhi badli nahi


def test_email_change_token_carries_old_and_new_email(auth_client, user, mailoutbox):
    request_change(auth_client, "NEW@Example.com")

    payload = read_email_change_token(extract_token(mailoutbox[0]))

    assert payload == {"uid": user.pk, "old": "user@example.com", "new": "new@example.com"}


def test_email_change_rejects_wrong_password(auth_client, user, mailoutbox):
    response = request_change(auth_client, "new@example.com", password="galat")

    assert response.status_code == 400
    assert "password" in response.json()
    assert len(mailoutbox) == 0


@pytest.mark.parametrize("new_email", ["user@example.com", "USER@Example.com"])
def test_email_change_rejects_the_current_email(auth_client, new_email):
    response = request_change(auth_client, new_email)
    assert response.status_code == 400
    assert "new_email" in response.json()


def test_email_change_rejects_email_of_another_user(auth_client):
    User.objects.create_user(email="taken@example.com", password=PASSWORD)
    response = request_change(auth_client, "TAKEN@example.com")
    assert response.status_code == 400
    assert "new_email" in response.json()


def test_email_change_rejects_email_of_a_soft_deleted_user(auth_client):
    gone = User.objects.create_user(email="gone@example.com", password=PASSWORD)
    gone.delete()
    assert request_change(auth_client, "gone@example.com").status_code == 400


def test_email_change_rejects_invalid_format(auth_client):
    assert request_change(auth_client, "not-an-email").status_code == 400


@pytest.mark.parametrize("body", [{}, {"new_email": "new@example.com"}, {"password": PASSWORD}])
def test_email_change_needs_both_fields(auth_client, body):
    response = auth_client.post(reverse("authnest:email-change"), body, format="json")
    assert response.status_code == 400


def test_email_change_returns_503_when_mail_cannot_be_sent(auth_client, monkeypatch):
    def boom(user, new_email):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("authnest.views.send_email_change_email", boom)

    assert request_change(auth_client, "new@example.com").status_code == 503


def test_phone_only_user_can_request_an_email(db, mailoutbox):
    phone_user = User.objects.create_user(phone="+919876543210", password=PASSWORD)

    response = request_change(client_for(phone_user), "added@example.com")

    assert response.status_code == 200
    assert mailoutbox[0].to == ["added@example.com"]


def test_email_change_is_blocked_for_a_soft_deleted_user(auth_client, user):
    user.delete()
    assert request_change(auth_client, "new@example.com").status_code == 401


# ======================= email change: confirm =======================

def test_full_flow_request_then_confirm(auth_client, api_client, user, mailoutbox):
    request_change(auth_client, "new@example.com")
    token = extract_token(mailoutbox[0])

    response = confirm(api_client, token)  # api_client login nahi hai, phir bhi chalna chahiye

    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
    user.refresh_from_db()
    assert user.email == "new@example.com"
    assert user.is_email_verified is True


def test_confirm_sends_a_notice_to_the_old_address(auth_client, api_client, user, mailoutbox):
    request_change(auth_client, "new@example.com")
    confirm(api_client, extract_token(mailoutbox[0]))

    assert len(mailoutbox) == 2
    assert mailoutbox[1].to == ["user@example.com"]
    assert mailoutbox[1].subject == "Aapki email badal di gayi hai"


def test_confirm_link_works_only_once(api_client, user):
    token = make_email_change_token(user, "new@example.com")

    assert confirm(api_client, token).status_code == 200
    assert confirm(api_client, token).status_code == 400


def test_login_works_with_the_new_email_only(api_client, user):
    confirm(api_client, make_email_change_token(user, "new@example.com"))

    assert login(api_client, "new@example.com").status_code == 200
    assert login(api_client, "user@example.com").status_code == 401


@pytest.mark.parametrize("token", ["", "garbage", "abc:def:ghi"])
def test_confirm_rejects_bad_token(api_client, token):
    response = confirm(api_client, token)
    assert response.status_code == 400
    assert "token" in response.json()


def test_confirm_rejects_expired_token(api_client, user, settings):
    token = make_email_change_token(user, "new@example.com")
    settings.AUTHNEST = {"EMAIL_VERIFICATION_TIMEOUT": -1}

    assert confirm(api_client, token).status_code == 400
    user.refresh_from_db()
    assert user.email == "user@example.com"


def test_confirm_rejects_a_token_made_for_another_purpose(api_client, user):
    assert confirm(api_client, make_password_reset_token(user)).status_code == 400


def test_confirm_rejects_token_if_email_changed_in_between(api_client, user):
    token = make_email_change_token(user, "new@example.com")
    user.email = "someone-else@example.com"
    user.save()

    assert confirm(api_client, token).status_code == 400


def test_confirm_fails_if_the_new_email_was_taken_meanwhile(api_client, user):
    token = make_email_change_token(user, "new@example.com")
    User.objects.create_user(email="new@example.com", password=PASSWORD)

    response = confirm(api_client, token)

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.email == "user@example.com"


def test_confirm_rejects_token_of_a_soft_deleted_user(api_client, user):
    token = make_email_change_token(user, "new@example.com")
    user.delete()
    assert confirm(api_client, token).status_code == 400


def test_phone_only_user_can_add_an_email(api_client, mailoutbox):
    phone_user = User.objects.create_user(phone="+919876543210", password=PASSWORD)
    token = make_email_change_token(phone_user, "added@example.com")

    response = confirm(api_client, token)

    assert response.status_code == 200
    phone_user.refresh_from_db()
    assert phone_user.email == "added@example.com"
    assert phone_user.is_email_verified is True
    assert len(mailoutbox) == 0  # purani email thi hi nahi, to notice nahi


def test_changing_email_does_not_log_the_user_out(api_client, user):
    tokens = issue_tokens(user)

    confirm(api_client, make_email_change_token(user, "new@example.com"))

    AuthnestRefreshToken(tokens["refresh"])  # TokenError nahi aana chahiye


# ======================= account delete =======================

def test_delete_account_needs_login(api_client):
    assert delete_account(api_client).status_code == 401


def test_delete_account_only_accepts_post(auth_client):
    assert auth_client.delete(reverse("authnest:account-delete")).status_code == 405


def test_delete_account_rejects_wrong_password(auth_client, user):
    response = delete_account(auth_client, password="galat")

    assert response.status_code == 400
    assert "password" in response.json()
    assert User.objects.filter(pk=user.pk).exists()


def test_delete_account_needs_a_password(auth_client):
    response = auth_client.post(reverse("authnest:account-delete"), {}, format="json")
    assert response.status_code == 400


def test_delete_account_soft_deletes_by_default(auth_client, user):
    response = delete_account(auth_client)

    assert response.status_code == 200
    assert not User.objects.filter(pk=user.pk).exists()
    deleted = User.all_objects.get(pk=user.pk)
    assert deleted.deleted_at is not None
    assert deleted.is_active is False


def test_delete_account_sends_a_goodbye_mail(auth_client, user, mailoutbox):
    delete_account(auth_client)

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["user@example.com"]
    assert mailoutbox[0].subject == "Aapka account delete ho gaya hai"
    assert "ab login nahi ho sakega" in mailoutbox[0].body


def test_delete_account_clears_the_cookie_in_cookie_mode(auth_client):
    response = delete_account(auth_client)
    assert response.cookies[COOKIE]["max-age"] == 0


def test_delete_account_touches_no_cookie_in_body_mode(auth_client, settings):
    settings.AUTHNEST = {"REFRESH_TOKEN_IN_COOKIE": False}
    response = delete_account(auth_client)
    assert COOKIE not in response.cookies


def test_everything_stops_working_after_delete(api_client, user):
    login_response = login(api_client, "user@example.com")
    access = login_response.json()["access"]
    other_device = issue_tokens(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    delete_account(api_client)

    assert api_client.get(reverse("authnest:profile")).status_code == 401
    assert api_client.post(reverse("authnest:token-refresh")).status_code == 401
    assert login(api_client, "user@example.com").status_code == 401
    assert_blacklisted(other_device["refresh"])


def test_email_stays_reserved_after_soft_delete(auth_client, api_client):
    delete_account(auth_client)

    response = api_client.post(
        reverse("authnest:register"),
        {"email": "user@example.com", "password": NEW_PASSWORD},
        format="json",
    )

    assert response.status_code == 400


def test_a_soft_deleted_account_can_be_restored(auth_client, api_client, user):
    delete_account(auth_client)
    User.all_objects.filter(pk=user.pk).restore()

    assert login(api_client, "user@example.com").status_code == 200


def test_delete_account_is_permanent_when_soft_delete_is_off(auth_client, user, settings, mailoutbox):
    settings.AUTHNEST = {"SOFT_DELETE": False}

    response = delete_account(auth_client)

    assert response.status_code == 200
    assert not User.all_objects.filter(pk=user.pk).exists()
    assert "hamesha ke liye" in mailoutbox[0].body


def test_email_can_be_reused_after_a_permanent_delete(auth_client, api_client, settings):
    settings.AUTHNEST = {"SOFT_DELETE": False}
    delete_account(auth_client)

    response = api_client.post(
        reverse("authnest:register"),
        {"email": "user@example.com", "password": NEW_PASSWORD},
        format="json",
    )

    assert response.status_code == 201


def test_phone_only_user_can_delete_the_account_without_mail(db, mailoutbox):
    phone_user = User.objects.create_user(phone="+919876543210", password=PASSWORD)

    response = delete_account(client_for(phone_user))

    assert response.status_code == 200
    assert not User.objects.filter(pk=phone_user.pk).exists()
    assert len(mailoutbox) == 0


def test_delete_still_succeeds_if_the_goodbye_mail_fails(auth_client, user, monkeypatch):
    def boom(user, to_email):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("authnest.views.send_account_deleted_email", boom)

    assert delete_account(auth_client).status_code == 200
    assert not User.objects.filter(pk=user.pk).exists()


def test_delete_is_atomic_user_stays_if_blacklisting_fails(auth_client, user, monkeypatch):
    def boom(user):
        raise RuntimeError("blacklist failed")

    monkeypatch.setattr("authnest.views.blacklist_all_tokens", boom)

    with pytest.raises(RuntimeError):
        delete_account(auth_client)

    assert User.objects.filter(pk=user.pk).exists()


# ---------- last superuser guard ----------

def test_the_last_superuser_cannot_delete_the_account(admin_user):
    response = delete_account(client_for(admin_user))

    assert response.status_code == 400
    assert User.objects.filter(pk=admin_user.pk).exists()


def test_a_superuser_can_delete_when_another_active_one_exists(admin_user):
    User.objects.create_superuser(username="admin2", email="a2@example.com", password=PASSWORD)

    assert delete_account(client_for(admin_user)).status_code == 200


def test_a_soft_deleted_superuser_does_not_count_as_another(admin_user):
    second = User.objects.create_superuser(username="admin2", email="a2@example.com", password=PASSWORD)
    second.delete()

    assert delete_account(client_for(admin_user)).status_code == 400


def test_an_inactive_superuser_does_not_count_as_another(admin_user):
    second = User.objects.create_superuser(username="admin2", email="a2@example.com", password=PASSWORD)
    second.is_active = False
    second.save()

    assert delete_account(client_for(admin_user)).status_code == 400


def test_a_normal_user_can_delete_even_if_only_one_superuser_exists(auth_client, admin_user):
    assert delete_account(auth_client).status_code == 200