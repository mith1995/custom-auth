# Settings reference

Configure the package with one dictionary in your Django settings:

```python
AUTHNEST = {
    "USER_LOGIN_METHODS": ["email", "phone"],
    "SOFT_DELETE": False,
}
```

Only the keys you set are overridden. The rest use the defaults below. Wrong values raise `ImproperlyConfigured` when Django starts. Check key names carefully: a misspelled key is not reported yet and is simply ignored.

## Login methods

- `USER_LOGIN_METHODS` (default `["email"]`): which identifiers a normal user can log in with. Allowed values are `"email"` and `"phone"`. With one method, that identifier is required at registration. With both, at least one is required.
- `ADMIN_LOGIN_METHODS` (default `["username"]`): identifiers accepted by the admin login endpoint (staff users). Allowed values are `"username"` and `"email"`.

## Email verification

- `REQUIRE_EMAIL_VERIFICATION` (default `True`): users with an email must verify it before they can log in. A user who registered with a phone number only is not blocked.
- `EMAIL_VERIFICATION_TIMEOUT` (default 86400): seconds a verification link stays valid. Email change confirmation links use the same timeout.
- `PASSWORD_RESET_TIMEOUT` (default 3600): seconds a reset link stays valid. This is the package setting, not Django's own `PASSWORD_RESET_TIMEOUT`.

## Frontend links

- `FRONTEND_URL` (default `"http://localhost:5173"`): base URL of your frontend, used to build email links.
- `VERIFY_EMAIL_PATH` (default `"/verify-email"`)
- `RESET_PASSWORD_PATH` (default `"/reset-password"`)
- `CONFIRM_EMAIL_CHANGE_PATH` (default `"/confirm-email-change"`)

Paths must be paths (start with `/`), not full URLs. The final link looks like `FRONTEND_URL + PATH + "?token=..."`.

## Tokens

- `ACCESS_TOKEN_LIFETIME` (default 900): seconds, 15 minutes. Keep it short, because an access token that was already issued stays valid until it expires, even after logout or a password change.
- `REFRESH_TOKEN_LIFETIME` (default 604800): seconds, 7 days.
- `REFRESH_TOKEN_ROTATION` (default `True`): every refresh returns a new refresh token and blacklists the old one.
- `REFRESH_TOKEN_IN_COOKIE` (default `True`): the refresh token is stored in an httpOnly cookie and is not in the response body. If `False`, it is returned in the response body and the client sends it in the body of refresh and logout requests.

The package uses its own lifetimes and does not change your project's `SIMPLE_JWT` settings.

## Refresh cookie

Used only when `REFRESH_TOKEN_IN_COOKIE` is `True`.

- `REFRESH_COOKIE_NAME` (default `"authnest_refresh"`): cookie name
- `REFRESH_COOKIE_PATH` (default `"/"`): path the browser sends the cookie to
- `REFRESH_COOKIE_SECURE` (default `None`): `None` means automatic, the cookie is Secure when `DEBUG` is off. Set `True` or `False` to force it.
- `REFRESH_COOKIE_SAMESITE` (default `"Lax"`): `"Lax"`, `"Strict"` or `"None"`.

During local development keep `DEBUG = True` so the cookie is not marked Secure. Otherwise clients will not send it over plain `http://`.

## Profile

- `PROFILE_PICTURE_MAX_SIZE` (default 2 MB, in bytes): largest accepted profile picture.

## Soft delete

- `SOFT_DELETE` (default `True`): when on, deleting a user marks the row as deleted (`deleted_at` is set and `is_active` becomes `False`) instead of removing it. Deleting a user who is already soft deleted removes the row permanently. When off, every delete is permanent.

Rules to know:

- The email and phone of a soft-deleted user stay reserved. Registering again with them fails until the user is hard deleted.
- `User.objects` returns only users that are not deleted. `User.all_objects` returns everyone.
- The Django admin hides the soft-delete filter and the restore action when `SOFT_DELETE` is `False`.
- If you switch `SOFT_DELETE` from `True` to `False`, purge the existing soft-deleted rows first. They will otherwise stay hidden in the database and keep their email and phone reserved.

## Reserved

These keys exist but do nothing yet: `ENABLE_2FA` and `SEND_EMAILS_ASYNC`. They are placeholders for later releases.
