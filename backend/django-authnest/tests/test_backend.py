import pytest
from django.contrib.auth import authenticate

from authnest.models import User
from tests.constants import PASSWORD

pytestmark = pytest.mark.django_db


@pytest.fixture
def phone_user():
    return User.objects.create_user(
        email="p@example.com", phone="+919876543210", password=PASSWORD
    )


def login(identifier, password=PASSWORD, scope="user"):
    return authenticate(username=identifier, password=password, scope=scope)


# ---------- normal user ----------

def test_user_can_login_with_email(user):
    assert login("user@example.com") == user


def test_email_login_ignores_case_and_spaces(user):
    assert login("  USER@Example.COM ") == user


def test_wrong_password_returns_none(user):
    assert login("user@example.com", password="galat") is None


def test_unknown_user_returns_none(db):
    assert login("koi@nahi.com") is None


def test_phone_login_is_off_by_default(phone_user):
    assert login("+919876543210") is None


def test_phone_login_works_when_enabled(phone_user, settings):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["email", "phone"]}
    assert login("+919876543210") == phone_user
    assert login("+91 98765 43210") == phone_user


def test_email_login_fails_when_only_phone_is_allowed(phone_user, settings):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["phone"]}
    assert login("p@example.com") is None


def test_generated_username_cannot_be_used_to_login(user):
    assert login(user.username) is None


# ---------- admin ----------

def test_admin_can_login_with_username(admin_user):
    assert login("admin", scope="admin") == admin_user


def test_admin_email_login_is_off_by_default(admin_user):
    assert login("admin@example.com", scope="admin") is None


def test_admin_email_login_works_when_enabled(admin_user, settings):
    settings.AUTHNEST = {"ADMIN_LOGIN_METHODS": ["username", "email"]}
    assert login("admin@example.com", scope="admin") == admin_user


# ---------- scope separation ----------

def test_normal_user_cannot_login_as_admin(user):
    assert login("user@example.com", scope="admin") is None


def test_admin_cannot_login_as_normal_user(admin_user, settings):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["email"]}
    assert login("admin@example.com", scope="user") is None


def test_scope_defaults_to_admin(user):
    assert authenticate(username="user@example.com", password=PASSWORD) is None


def test_invalid_scope_returns_none(user):
    assert login("user@example.com", scope="superhero") is None


# ---------- inactive, deleted ----------

def test_inactive_user_cannot_login(user):
    user.is_active = False
    user.save()
    assert login("user@example.com") is None


def test_soft_deleted_user_cannot_login_until_restored(user):
    user.delete()
    assert login("user@example.com") is None

    User.all_objects.filter(pk=user.pk).restore()
    assert login("user@example.com") == user