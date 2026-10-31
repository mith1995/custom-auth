from django.conf import settings
from rest_framework.response import Response

from ..conf import authnest_settings

def _cookie_secure():
    value = authnest_settings.REFRESH_COOKIE_SECURE
    # None matlab auto: DEBUG band ho to Secure
    return (not settings.DEBUG) if value is None else value

def set_refresh_cookie(response, refresh_token):
    response.set_cookie(
        authnest_settings.REFRESH_COOKIE_NAME,
        refresh_token,
        max_age = authnest_settings.REFRESH_TOKEN_LIFETIME,
        httponly = True,
        secure = _cookie_secure(),
        samesite = authnest_settings.REFRESH_COOKIE_SAMESITE,
        path = authnest_settings.REFRESH_COOKIE_PATH,
    )

def delete_refresh_cookie(response):
    response.delete_cookie(
        authnest_settings.REFRESH_COOKIE_NAME,
        path = authnest_settings.REFRESH_COOKIE_PATH,
        samesite = authnest_settings.REFRESH_COOKIE_SAMESITE,
    )

def read_refresh_token(request):
    if authnest_settings.REFRESH_TOKEN_IN_COOKIE:
        return request.COOKIES.get(authnest_settings.REFRESH_COOKIE_NAME)
    data = request.data
    return data.get("refresh") if hasattr(data, "get") else None

def build_token_response(tokens, extra=None, status_code=200):
    data = {"access": tokens["access"]}
    if extra:
        data.update(extra)

    cookie_mode = authnest_settings.REFRESH_TOKEN_IN_COOKIE
    if not cookie_mode:
        data["refresh"] = tokens["refresh"]

    response = Response(data, status=status_code)
    if cookie_mode:
        set_refresh_cookie(response, tokens["refresh"])
    return response