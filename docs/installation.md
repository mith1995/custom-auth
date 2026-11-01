# Installation

django-authnest is a reusable Django REST Framework app. It gives you a custom user model, login with JWT, email verification, password flows, profile, and optional soft delete.

## Requirements

- Python version as declared in the package metadata (see `requires-python` on PyPI)
- Django 5.1 or newer
- Django REST Framework, djangorestframework-simplejwt and Pillow (installed automatically)

## Install

```
pip install django-authnest
```

## Project settings

Add the apps. `token_blacklist` is required because logout and password change blacklist refresh tokens.

```python
INSTALLED_APPS = [
    # ... django apps ...
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "authnest",
]
```

Use the package user model and login backend. Set `AUTH_USER_MODEL` before you run the first `migrate`, because Django cannot switch the user model on a database that already has migrations applied.

```python
AUTH_USER_MODEL = "authnest.User"

AUTHENTICATION_BACKENDS = [
    "authnest.backends.AuthnestBackend",
]
```

Set the sender address for emails.

```python
DEFAULT_FROM_EMAIL = "no-reply@example.com"
```

## Email backend

Django 6.1 and newer use the `MAILERS` setting. For development, the console backend prints emails in the terminal that runs `runserver`:

```python
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
```

On older Django versions use `EMAIL_BACKEND` instead. Do not define both. In production, point the backend at a real SMTP or provider backend.

## Media files (profile pictures)

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

In development, serve media from your root `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## URLs

```python
from django.urls import include, path

urlpatterns = [
    path("auth/", include("authnest.urls")),
]
```

All endpoints in the API reference are relative to this prefix.

## Create the tables

```
python manage.py migrate
python manage.py createsuperuser
```

## Configure the package

All package options live in one dictionary called `AUTHNEST`. Every key is optional. See `settings.md`.

```python
AUTHNEST = {
    "USER_LOGIN_METHODS": ["email"],
    "FRONTEND_URL": "http://localhost:5173",
}
```

A wrong value stops the server at startup with `ImproperlyConfigured`, so mistakes show up immediately and not on the first request.

## Frontend

Email links (verify email, reset password, confirm email change) point to your frontend, not to the API. Set `FRONTEND_URL` and the path settings so the links match your frontend routes. Your frontend page reads the `token` query parameter and sends it to the matching API endpoint.

If your frontend runs on a different origin and you keep the refresh token in the httpOnly cookie, you need CORS with credentials (for example `django-cors-headers` with `CORS_ALLOW_CREDENTIALS = True`) and `withCredentials: true` in your HTTP client.
