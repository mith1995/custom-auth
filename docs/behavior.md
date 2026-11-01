# Design notes and limitations

This page explains the decisions behind the package, so you know what to expect and what is not included.

## Security decisions

- Signed tokens: verification, reset and email-change links are signed with Django's signing module, each with its own salt, so a token for one purpose cannot be used for another. They expire according to the timeout settings.
- Single-use links without a database table: the reset token contains a fingerprint of the current password hash, and the email-change token contains the old email. When the password or email changes, the old link stops working by itself.
- No account discovery: forgot-password and resend-verification always return the same response, and registration reports "already exists" without saying whether the account is deleted.
- Password required for sensitive actions: changing the email and deleting the account both ask for the password.
- Refresh token storage: by default the refresh token lives in an httpOnly cookie, so JavaScript cannot read it. Use body mode only if your client cannot use cookies.
- Tokens after password change: all refresh tokens are blacklisted. An access token that was already issued works until it expires, so keep `ACCESS_TOKEN_LIFETIME` short.
- Database safety: the password change and the token blacklisting happen in one transaction.

## Users

- A user must have an email or a phone number (a database constraint enforces it).
- Normal users get an automatic username like `user_xxxx`. They log in with email or phone.
- Email and phone are normalized before they are stored and compared.

## Not included yet

- Two-factor authentication (TOTP) is planned for a later release. `ENABLE_2FA` is a placeholder.
- Phone verification and SMS OTP: a phone number works as a login identifier, but it is not verified, and password reset by phone is not available. A user without an email cannot use forgot-password.
- Rate limiting (throttling) of login and email endpoints. Add DRF throttling in your project for now.
- Social login (Google, GitHub) is planned.
- Asynchronous email sending: `SEND_EMAILS_ASYNC` is a placeholder. Emails are sent inside the request.
- Only English messages and templates, no translation files yet.

## Customising emails

Email templates live in `authnest/templates/authnest/email/`. To change one, create a file with the same path in your own project's templates folder, and make sure your app (or `DIRS`) comes before `authnest` in the template search order. Each email has an HTML and a text version.

## Versioning

The package follows semantic versioning. While the version starts with `0.`, minor releases may change behaviour. Check the changelog before upgrading.
