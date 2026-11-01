# django-authnest

[![PyPI](https://img.shields.io/pypi/v/django-authnest)](https://pypi.org/project/django-authnest/)
[![CI](https://github.com/mith1995/custom-auth/actions/workflows/ci.yml/badge.svg)](https://github.com/mith1995/custom-auth/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/mith1995/custom-auth/blob/main/backend/django-authnest/LICENSE)

Reusable authentication for Django REST Framework projects. Add it once, configure it with one settings dictionary, and skip rewriting login, registration and password flows in every project.

## Features

- Login by email, phone or both for users, and by username, email or both for admins (separate settings)
- JWT access and refresh tokens, with rotation and blacklisting
- Refresh token in an httpOnly cookie or in the response body (your choice)
- Registration with email verification link
- Forgot, reset and change password with HTML and text emails
- Profile with picture, name and date of birth
- Email change confirmed through a link sent to the new address
- Account delete, with optional soft delete and restore in the Django admin
- Settings are validated at startup, so a wrong value fails fast

## Quick start

Install:

```
pip install django-authnest
```

Add to your Django settings:

```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "authnest",
]

AUTH_USER_MODEL = "authnest.User"
AUTHENTICATION_BACKENDS = ["authnest.backends.AuthnestBackend"]
DEFAULT_FROM_EMAIL = "no-reply@example.com"

AUTHNEST = {
    "USER_LOGIN_METHODS": ["email"],
    "FRONTEND_URL": "http://localhost:5173",
}
```

Add the URLs:

```python
from django.urls import include, path

urlpatterns = [
    path("auth/", include("authnest.urls")),
]
```

Create the tables:

```
python manage.py migrate
```

Set `AUTH_USER_MODEL` before the first `migrate`. Django cannot switch the user model on a database that already has migrations applied.

On Django 6.1 and newer, configure email with `MAILERS` instead of `EMAIL_BACKEND`. The full setup, including email and media settings, is in the installation guide.

## Documentation

- [Installation](https://github.com/mith1995/custom-auth/blob/main/docs/installation.md)
- [Settings reference](https://github.com/mith1995/custom-auth/blob/main/docs/settings.md)
- [API reference](https://github.com/mith1995/custom-auth/blob/main/docs/api.md)
- [Design notes and limitations](https://github.com/mith1995/custom-auth/blob/main/docs/behavior.md)

## Endpoints at a glance

All paths are relative to the prefix you choose in `urls.py`.

- `POST register/`, `verify-email/`, `resend-verification/`
- `POST login/`, `admin/login/`, `token/refresh/`, `logout/`
- `POST forgot-password/`, `reset-password/`, `change-password/`
- `GET, PATCH profile/` and `DELETE profile/picture/`
- `POST email/change/` and `email/change/confirm/`
- `POST account/delete/`

## Status

Alpha. The API may change between `0.x` releases, so pin the version in production. Planned next: two-factor authentication, rate limiting, social login, and a React reference frontend (in progress in this repository).

## Development

```
git clone https://github.com/mith1995/custom-auth.git
cd custom-auth/backend/django-authnest
pip install -e ".[dev]"
pytest
```

## License

MIT
