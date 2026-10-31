import pytest

from django.core.exceptions import ImproperlyConfigured
from authnest.conf import authnest_settings

def test_default_value_when_not_overridden():
    assert authnest_settings.ENABLE_2FA is False
    assert authnest_settings.USER_LOGIN_METHODS == ["email"]

def test_project_settings_overrides_default(settings):
    settings.AUTHNEST = {"SOFT_DELETE": False}
    assert authnest_settings.SOFT_DELETE is False

def test_unknown_setting_raises_attribute_error():
    with pytest.raises(AttributeError):
        authnest_settings.NAHI_HAI

def test_valid_config_passes_validation(settings):
    settings.AUTHNEST = {"USER_LOGIN_METHODS": ["email", "phone"]}
    authnest_settings.validate()

@pytest.mark.parametrize(
    "config",
    [
        {"USER_LOGIN_METHODS": []},
        {"USER_LOGIN_METHODS": ['abc']},
        {"USER_LOGIN_METHODS": 'email'},
        {"ADMIN_LOGIN_METHODS": ["phone"]},
        {"SOFT_DELETE": "yes"},
        {"ACCESS_TOKEN_LIFETIME": 0},
        {"REFRESH_TOKEN_LIFETIME": True},
        {"REFRESH_TOKEN_IN_COOKIE": "yes"},
        {"REFRESH_COOKIE_SAMESITE": "lax"},
        {"PROFILE_PICTURE_MAX_SIZE": 0},
        {"PROFILE_PICTURE_MAX_SIZE": "2mb"},
    ]
)

def test_invalid_config_raises(settings, config):
    settings.AUTHNEST = config
    with pytest.raises(ImproperlyConfigured):
        authnest_settings.validate()