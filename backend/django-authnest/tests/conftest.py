import pytest
from rest_framework.test import APIClient

from authnest.models import User
from authnest.services.tokens import issue_tokens
from tests.constants import PASSWORD

@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com", password=PASSWORD, is_email_verified=True
    )

@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
    return client

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password=PASSWORD
    )