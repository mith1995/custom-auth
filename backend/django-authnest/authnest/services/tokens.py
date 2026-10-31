import hashlib
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.core import signing
from ..conf import authnest_settings

EMAIL_VERIFY_SALT = "authnest.email-verify"
PASSWORD_RESET_SALT = "authnest.password-reset"
EMAIL_CHANGE_SALT = "authnest.email-change"

def make_email_verification_token(user):
    return signing.dumps(
        {"uid": user.pk, "email": user.email},
        salt=EMAIL_VERIFY_SALT
    )

def read_email_verification_token(token):
    # Valid ho to payload dict, warna signing.BadSignature / SignatureExpired
    return signing.loads(
        token,
        salt=EMAIL_VERIFY_SALT,
        max_age=authnest_settings.EMAIL_VERIFIFCATION_TIMEOUT
    )

class AuthnestRefreshToken(RefreshToken):
    """Refresh token jiski lifetime AUTHnest settings se aati hai, SIMPLE_JWT se nahi."""

    @property
    def lifetime(self):
        return timedelta(seconds=authnest_settings.REFRESH_TOKEN_LIFETIME)

def make_access_token(refresh):
    access = refresh.access_token
    access.set_exp(
        lifetime=timedelta(seconds=authnest_settings.ACCESS_TOKEN_LIFETIME)
    )
    return access

def issue_tokens(user):
    refresh = AuthnestRefreshToken.for_user(user)
    access = make_access_token(refresh)
    return {"access": str(access), "refresh": str(refresh)}

def password_fingerprint(user):
    # Password hash ka ek hissa. Password badalte hi ye badal jata hai.
    return hashlib.sha256(user.password.encode()).hexdigest()[:20]

def make_password_reset_token(user):
    return signing.dumps(
        {"uid": user.pk, "pwd": password_fingerprint(user)},
        salt=PASSWORD_RESET_SALT
    )

def read_password_reset_token(token):
    # Valid ho to payload dict, warna signing.BadSignature / SignatureExpired
    return signing.loads(
        token,
        salt=PASSWORD_RESET_SALT,
        max_age=authnest_settings.PASSWORD_RESET_TIMEOUT,
    )

def blacklist_all_tokens(user):
    # Lazy import: blacklist app ke models app-loading ke baad hi import ho sakte hain
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)

def make_email_change_token(user, new_email):
    return signing.dumps(
        {"uid": user.pk, "old": user.email, "new": new_email},
        salt=EMAIL_CHANGE_SALT
    )

def read_email_change_token(token):
    # Valid ho to payload dict, warna signing.BadSignature / SignatureExpired
    return signing.loads(
        token,
        salt=EMAIL_CHANGE_SALT,
        max_age=authnest_settings.EMAIL_VERIFICATION_TIMEOUT,
    )
