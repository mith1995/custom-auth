# API reference

All paths are relative to the prefix you chose in `urls.py` (the examples use `/auth/`). Request and response bodies are JSON unless stated otherwise.

Endpoints marked "Bearer" need the header `Authorization: Bearer <access token>`.

## Registration and email verification

### POST /auth/register/

Creates a user and sends a verification email (if an email was given and `REQUIRE_EMAIL_VERIFICATION` is on). Which identifiers are accepted depends on `USER_LOGIN_METHODS`. The password must pass Django's password validators.

- 400 for invalid input, weak password, or when the email or phone already exists. The "already exists" message is the same for live and soft-deleted accounts.
- If sending the email fails, registration still succeeds and the error is logged.

### POST /auth/verify-email/

Body: `{"token": "..."}`. Marks the email as verified. Calling it twice with the same valid token is fine. An invalid, expired or outdated token returns 400. A link becomes invalid if the user's email changed after it was issued.

### POST /auth/resend-verification/

Body: `{"email": "..."}`. The response is always the same, whether or not the email is registered, so the endpoint cannot be used to discover accounts.

## Login, tokens and logout

### POST /auth/login/

Body: `{"identifier": "...", "password": "..."}`. The identifier is an email or a phone number, according to `USER_LOGIN_METHODS`.

- Success: the access token is returned in the response body. The refresh token is set as an httpOnly cookie, or returned in the body when `REFRESH_TOKEN_IN_COOKIE` is `False`. It is never in both places.
- 401 for a wrong identifier or password (one message for both).
- 403 when the email is not verified yet.

### POST /auth/admin/login/

Same body. Only staff users can log in here, using `ADMIN_LOGIN_METHODS`. A normal user gets 401 here and an admin gets 401 on `/auth/login/`.

### POST /auth/token/refresh/

Cookie mode: send the request with cookies and no body. Body mode: send `{"refresh": "..."}`. Returns a new access token, and with rotation on, a new refresh token (the old one is blacklisted). Returns 401 for an invalid, expired or blacklisted token, and for a deleted user.

### POST /auth/logout/

Blacklists the refresh token and removes the cookie. It reports success even when the token was already invalid, because the user is logged out either way.

## Password

### POST /auth/forgot-password/

Body: `{"email": "..."}`. Always returns the same response. If the account exists, a reset link is emailed.

### POST /auth/reset-password/

Body: `{"token": "...", "password": "..."}`. Sets the new password, blacklists all refresh tokens of the user and sends a "password changed" email. The user is not logged in automatically. The link works only once: it stops working as soon as the password changes. A weak password returns 400 and the link stays usable.

### POST /auth/change-password/ (Bearer)

Body: `{"old_password": "...", "new_password": "..."}`. Changes the password and blacklists all refresh tokens, including the one of the current device, so the user logs in again everywhere. 400 for a wrong old password or a new password equal to the old one.

## Profile (Bearer)

### GET /auth/profile/

Returns the profile of the logged-in user.

### PATCH /auth/profile/

Editable fields: `first_name`, `last_name`, `dob`, `profile_picture`. Send JSON, or multipart form-data when uploading a picture. Email, phone and the verified flags cannot be changed here. The old picture file is removed from storage when a new one is uploaded. `dob` cannot be in the future or more than 120 years ago. Pictures larger than `PROFILE_PICTURE_MAX_SIZE` are rejected. `PUT` is not supported.

### DELETE /auth/profile/picture/

Removes the profile picture. Returns 204.

## Email change

### POST /auth/email/change/ (Bearer)

Body: `{"new_email": "...", "password": "..."}`. The password is required because the email is a login identifier. A confirmation link is sent to the new address, and the old email keeps working until the link is used. 400 for a wrong password, the same email, or an email that is already taken (including soft-deleted accounts). 503 if the email could not be sent.

### POST /auth/email/change/confirm/

Body: `{"token": "..."}`. No login needed, so the link can be opened on any device. Changes the email, marks it verified and sends a notice to the old address. The link works once. Refresh tokens are not blacklisted by an email change.

## Delete account

### POST /auth/account/delete/ (Bearer)

Body: `{"password": "..."}`. This is a POST and not a DELETE because the password must travel in the body. All refresh tokens are blacklisted and the user is deleted (soft or permanent, depending on `SOFT_DELETE`), then a confirmation email is sent. The last active superuser cannot delete their own account (400). The old access token stops working immediately, because deleted users are not found.
