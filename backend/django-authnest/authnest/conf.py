from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULTS = {
    "SOFT_DELETE": True,
    "USER_LOGIN_METHODS": ["email"],
    "ADMIN_LOGIN_METHODS": ["username"],
    "REQUIRE_EMAIL_VERIFICATION": True,
    "ENABLE_2FA": False,
    "SEND_EMAILS_ASYNC": False,
    "FRONTEND_URL": "http://localhost:5173",
    "VERIFY_EMAIL_PATH": "/verify-email", # frontend ka route jahan verify link khulega (jaise /verify-email)
    "RESET_PASSWORD_PATH": "/reset-password", # reset password page ka route (jaise /reset-password)
    "EMAIL_VERIFICATION_TIMEOUT": 24 * 3600, # verify link kitne seconds me expire ho (jaise 1 din)
    "PASSWORD_RESET_TIMEOUT": 3600, # reset link ki expiry (jaise 1 ghanta)
    "ACCESS_TOKEN_LIFETIME": 15 * 60,           # seconds (15 minute)
    "REFRESH_TOKEN_LIFETIME": 7 * 24 * 3600,    # seconds (7 din)
    "REFRESH_TOKEN_IN_COOKIE": True,            # True: httpOnly cookie, False: response body
    "REFRESH_TOKEN_ROTATION": True,             # har refresh par naya token, purana blacklist
    "REFRESH_COOKIE_NAME": "authnest_refresh",
    "REFRESH_COOKIE_PATH": "/",
    "REFRESH_COOKIE_SECURE": None,              # None = auto (DEBUG band ho to Secure)
    "REFRESH_COOKIE_SAMESITE": "Lax",
    "PROFILE_PICTURE_MAX_SIZE": 2 * 1024 * 1024, # 2MB
    "CONFIRM_EMAIL_CHANGE_PATH": "/confirm-email-change",
}  

ALLOWED_USER_LOGIN_METHODS = {"email", "phone"}
ALLOWED_ADMIN_LOGIN_METHODS = {"email", "username"}

class AuthnestSettings:
    def __getattr__(self, name):
        # settings.py me Authnest na ho to khali dict (lazy: access ke time padha)
        user_settings = getattr(settings, "AUTHNEST", {})

        if name in user_settings:
            return user_settings[name]
        if name in DEFAULTS:
            return DEFAULTS[name]
        raise AttributeError(f"Invalid Authnest setting: '{name}'")

    def validate(self):
        self.validate_methods("USER_LOGIN_METHODS", ALLOWED_USER_LOGIN_METHODS)
        self.validate_methods("ADMIN_LOGIN_METHODS", ALLOWED_ADMIN_LOGIN_METHODS)

        if not isinstance(self.SOFT_DELETE, bool):
            raise ImproperlyConfigured(
                "AUTHNEST['SOFT_DELETE'] must be True or False."
            )

        for name in ("ACCESS_TOKEN_LIFETIME", "REFRESH_TOKEN_LIFETIME"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ImproperlyConfigured(
                    f"AUTHNEST['{name}'] must be a positive integer (seconds)."
                )

        for name in ("REFRESH_TOKEN_IN_COOKIE", "REFRESH_TOKEN_ROTATION"):
            if not isinstance(getattr(self, name), bool):
                raise ImproperlyConfigured(
                    f"AUTHNEST['{name}'] must be True or False."
                )

        if self.REFRESH_COOKIE_SAMESITE not in ("Lax", "Strict", "None"):
            raise ImproperlyConfigured(
                "AUTHNEST['REFRESH_COOKIE_SAMESITE'] must be 'Lax', 'Strict', or 'None'."
            )

        if "rest_framework_simplejwt.token_blacklist" not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                "Add 'rest_framework_simplejwt.token_blacklist' to INSTALLED_APPS "
                "(Authnest needs it for logout and refresh token rotation)."
            )

        size = self.PROFILE_PICTURE_MAX_SIZE
        if isinstance(size, bool) or not (isinstance(size, int)) or size <= 0:
            raise ImproperlyConfigured(
                f"AUTHNEST['PROFILE_PICTURE_MAX_SIZE'] must be a positive integer (bytes)."
            )
        
    def validate_methods(self, setting_name, allowed):
        methods = getattr(self, setting_name)

        if not isinstance(methods, (list, tuple, set)) or not methods:
            raise ImproperlyConfigured(
                f"AUTHNEST['{setting_name}'] must be a non-empty list. "
                f"Allowed values: {sorted(allowed)}"
            )

        invalid = set(methods) - allowed
        if invalid:
            raise ImproperlyConfigured(
                f"AUTHNEST['{setting_name}'] has invalid values {sorted(invalid)}. "
                f"Allowed values: {sorted(allowed)}"
            )

authnest_settings = AuthnestSettings()