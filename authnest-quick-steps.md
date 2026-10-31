# Package Setup: Quick Steps (django-authnest)

## Folder structure

```
custom-auth/
|-- .gitignore
|-- backend/
|   |-- .venv/
|   |-- django-authnest/          (package, pip install wala)
|   |   |-- pyproject.toml
|   |   |-- README.md
|   |   +-- authnest/             (import name)
|   |       |-- __init__.py
|   |       |-- apps.py
|   |       +-- conf.py
|   +-- demo/                    (testing ke liye normal Django project)
|       |-- manage.py
|       +-- config/
+-- frontend/
    +-- react/                   (Vite app)
```

## Steps

### 1. Folders banao

```
mkdir custom-auth
cd custom-auth
mkdir backend frontend
cd backend
mkdir -p django-authnest/authnest
```

`authnest/` me `__init__.py` (khali) aur `apps.py` banao.

### 2. Virtualenv + dependencies (backend/ me)

```
python -m venv .venv
source .venv/bin/activate
pip install django djangorestframework djangorestframework-simplejwt
```

Windows: `.venv\Scripts\activate`

### 3. Demo project banao (backend/ me)

```
django-admin startproject config demo
```

### 4. Package files likho

- `django-authnest/pyproject.toml`: name, version, dependencies, packages find
- `authnest/apps.py`: `name = "authnest"` (folder ka naam nahi, import ka naam)

### 5. Package install karo (backend/ se, venv active)

```
pip install -e ./django-authnest
pip list
```

### 6. Demo me register karo

`demo/config/settings.py` ke `INSTALLED_APPS` me `"authnest"` add karo, phir:

```
cd demo
python manage.py runserver
```

Bina error ke chale to setup sahi hai.

### 7. Frontend

- `frontend/react/` banao
- Vite app ki andar ki saari files (hidden files bhi) isme daalo
- `node_modules` delete karke ye chalao:

```
cd frontend/react
npm install
npm run dev
```

### 8. `.gitignore` (root me, har pattern alag line me)

```
.venv/
venv/
__pycache__/
*.pyc
*.egg-info/
build/
dist/
db.sqlite3
media/
staticfiles/
.env
.env.*
!.env.example
node_modules/
*.log
.vscode/
.idea/
.DS_Store
```

`migrations/` ko ignore mat karna.

## Yaad rakhne wali baatein

- pip name (`django-authnest`) aur import name (`authnest`) alag hote hain
- `pip install -e` active virtualenv me install karta hai, folder me nahi
- `pyproject.toml` ke bina install nahi hoga
- Package ke andar migrations commit karni hain

## Package kaam kaise karta hai: Step 1 (conf.py) ho gaya

### `conf.py` me kya hai

- `DEFAULTS` dict: har setting ka default (login methods, email verification, 2FA, `FRONTEND_URL`, paths, timeouts)
- `ALLOWED_USER_LOGIN_METHODS` (`email`, `phone`) aur `ALLOWED_ADMIN_LOGIN_METHODS` (`username`, `email`)
- `AuthnestSettings` class: `__getattr__` pehle `settings.AUTHNEST` me dhundhta hai, phir `DEFAULTS` me, warna `AttributeError`
- `validate()`: galat ya khali login methods par `ImproperlyConfigured`
- `authnest_settings = AuthnestSettings()`: package me kahin bhi `from authnest.conf import authnest_settings`

### Files kahan rehti hain

- `pyproject.toml` sirf `django-authnest/` me
- `__init__.py`, `apps.py`, `conf.py` teeno `authnest/` ke andar

### Settings ke rules

- Host sirf `FRONTEND_URL` me, `VERIFY_EMAIL_PATH` aur `RESET_PASSWORD_PATH` me sirf path (`/verify-email`)
- Email link banate waqt `FRONTEND_URL.rstrip("/")` use karna (Step 3)

### Test kaise kiya (demo/ me, venv active)

```
cd demo
python manage.py shell
```

```python
from authnest.conf import authnest_settings
authnest_settings.ENABLE_2FA
authnest_settings.NAHI_HAI
authnest_settings.validate()
```

- Default value aani chahiye, `NAHI_HAI` par `AttributeError`, `validate()` chup-chaap pass
- `manage.py` `demo/` me hai, `backend/` me nahi
- Naya terminal kholne par venv dobara activate karo
- `AUTHNEST` me galat value (`["abc"]`, `[]`) daal ke `validate()` check kiya, test ke baad hata diya

### Errors jo aaye aur fix

- `manage.py` not found: `demo/` me jao
- `No module named authnest`: venv activate karo, `pip install -e ./django-authnest`
- `No module named authnest.conf`: `conf.py` `authnest/` ke andar honi chahiye
- `validate_methods` ka naam `validate()` me aur method me same rakho, warna `__getattr__` confusing `AttributeError` deta hai

## Step 2 ho gaya: User model + manager + login backend

### Folder me ye files jude (`authnest/` ke andar)

```
authnest/
|-- models.py        (User model)
|-- managers.py      (UserQuerySet, UserManager, AllUsersManager)
|-- utils.py         (normalize_email, normalize_phone)
|-- backends.py      (AuthnestBackend)
+-- migrations/
    +-- __init__.py
```

### Kya hai

- `models.py`: `AbstractBaseUser + PermissionsMixin`. Identity: `email`, `phone`, `username` (teeno `null=True, blank=True, unique=True`). Profile, status aur `deleted_at` fields. `USERNAME_FIELD = "username"`, `REQUIRED_FIELDS = ["email"]`, aur `CheckConstraint` (email ya phone mein se ek zaroori)
- Soft delete: `delete()` row mark karta hai, `restore()`, `hard_delete()`. `AUTHNEST["SOFT_DELETE"] = False` karne par `delete()` asli delete karta hai
- `managers.py`: `objects` sirf alive users, `all_objects` sab. Queryset ke `delete`, `hard_delete`, `restore` par `queryset_only = True`
- `backends.py`: `AuthnestBackend.authenticate(request, username, password, scope)`. `scope="user"` normal users (`USER_LOGIN_METHODS`), `scope="admin"` staff (`ADMIN_LOGIN_METHODS`)

### Demo me settings

- `AUTH_USER_MODEL = "authnest.User"` (pehli `migrate` se pehle)
- `AUTHENTICATION_BACKENDS = ["authnest.backends.AuthnestBackend"]`

### Commands

```
pip install pillow
python manage.py makemigrations authnest
python manage.py migrate
```

`pillow` ko `pyproject.toml` ki dependencies me bhi jodo. Purani `db.sqlite3` hatao agar `AUTH_USER_MODEL` baad me set kiya.

### Decisions

- Soft-deleted user ka email/phone reserved rehta hai, dobara register par "already exists". Wahi email dobara tabhi use hoga jab hard delete ho
- Registration ka duplicate check `all_objects` se hoga
- Register par deleted ya alive dono ke liye generic "already exists" message
- Normal user ka username auto-generate (`user_xxxx`), asli login email ya phone se
- Email verified hai ya nahi, ye check login view me hoga (Step 4), backend me nahi

### Errors jo aaye aur fix

- `authenticate()` har galti par chupchap `None` deta hai: shell restart karo, `settings.AUTHENTICATION_BACKENDS` print karo, backend ko seedha call karo
- `password is not None` ki jagah `password is None` likhna tha
- `create_user` ko positional arguments se call mat karo, hamesha `email=`, `phone=`, `password=` ke saath (warna password phone me chala jata hai)
- `from_queryset` ke methods manager par bhi aa jate hain: `queryset_only = True` lagao

## Step 3 ho gaya: Registration + email verification

### Folder me ye files jude (`authnest/` ke andar)

```
authnest/
|-- serializers.py   (RegisterSerializer, VerifyEmailSerializer, ResendVerificationSerializer)
|-- views.py         (RegisterView, VerifyEmailView, ResendVerificationView)
|-- urls.py
|-- services/
|   |-- __init__.py  (khali)
|   |-- tokens.py    (make / read email verification token)
|   +-- emails.py    (build_frontend_url, send_templated_email, send_verification_email)
+-- templates/authnest/email/
    |-- base.html
    |-- verify_email.html
    +-- verify_email.txt
```

### Endpoints (demo me `path("auth/", include("authnest.urls"))`)

- `POST /auth/register/`: user banata hai, verification email bhejta hai (agar email di ho aur `REQUIRE_EMAIL_VERIFICATION` True ho)
- `POST /auth/verify-email/` body `{"token": "..."}`: `is_email_verified=True` karta hai, dobara chalane par bhi 200
- `POST /auth/resend-verification/` body `{"email": "..."}`: response hamesha same (email exist kare ya na kare)

### Kaise kaam karta hai

- Token: `signing.dumps({"uid", "email"}, salt=...)`, expiry `EMAIL_VERIFICATION_TIMEOUT`. Email badalne par purana link invalid
- Link: `FRONTEND_URL` + `VERIFY_EMAIL_PATH` + `?token=...`, React page token ko API par POST karega
- Registration ka duplicate check `all_objects` se, aur `IntegrityError` pakadkar saaf error
- Sirf wahi identifier allowed jo `USER_LOGIN_METHODS` me hai. Ek method ho to wahi zaroori, dono ho to kam se kam ek
- Email bhejna fail ho to registration fail nahi hota, error log hota hai
- Phone-only user ka verification abhi nahi (SMS OTP baad ka optional feature)

### Demo me settings

- `INSTALLED_APPS` me `"rest_framework"`
- `DEFAULT_FROM_EMAIL = "no-reply@example.com"`
- Django 6.1+ me `EMAIL_BACKEND` nahi, `MAILERS` use hota hai:

```python
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
```

Console backend email ko `runserver` wali terminal me print karta hai, kisi inbox me nahi jati.

### `pyproject.toml` me

```toml
[tool.setuptools.package-data]
authnest = ["templates/**/*"]
```

### Test kaise kiya

- Shell: `send_verification_email(u)`, `read_email_verification_token(t)`, `t + "x"` par `BadSignature`, aur chhoti `EMAIL_VERIFICATION_TIMEOUT` se `SignatureExpired`
- Postman: register, duplicate register, soft-deleted email se register, kamzor password, dono identifier khali, verify (do baar), resend (registered aur anjaan email)
- Testing me token shell se banao: `make_email_verification_token(User.objects.get(pk=...))`

### Errors jo aaye aur fix

- `ImproperlyConfigured: Deprecated email settings ... when MAILERS is defined`: `EMAIL_BACKEND` hatao, `MAILERS` me `"BACKEND"` set karo
- `TemplateDoesNotExist: authnest/email/base.html`: folder ka naam `email` (singular) hona chahiye, `emails` nahi
- `no attribute 'DEFAULT_EMAIL_FROM'`: sahi naam `DEFAULT_FROM_EMAIL`
- Console me email kisi inbox me nahi aati, `runserver` terminal me print hoti hai
- Console token quoted-printable me print hota hai: shuru ka `3D`, line ke aakhir ka `=`, aur `%3A` hata ke `:` rakho (ya token shell se banao)
- `urlencode(params, safe=":")` se link me `:` waise hi rehta hai (optional)

## Step 4 ho gaya: Login + JWT + refresh + logout

### Folder me ye files jude/badle (`authnest/` ke andar)

```
authnest/
|-- exceptions.py      (InvalidCredentials 401, EmailNotVerified 403)
|-- serializers.py     (LoginSerializer, AdminLoginSerializer jude)
|-- views.py           (LoginView, AdminLoginView, RefreshView, LogoutView jude)
|-- urls.py            (4 naye routes)
+-- services/
    |-- tokens.py      (AuthnestRefreshToken, make_access_token, issue_tokens)
    +-- cookies.py     (set/delete/read refresh cookie, build_token_response)
```

### Endpoints

- `POST /auth/login/` body `{"identifier": "...", "password": "..."}`: normal users (`scope="user"`)
- `POST /auth/admin/login/`: staff users (`scope="admin"`), same body
- `POST /auth/token/refresh/`: refresh token cookie se (ya body `{"refresh": "..."}` se), rotation ke saath
- `POST /auth/logout/`: refresh token blacklist, cookie hatana

### Settings (`conf.py` DEFAULTS me)

- `ACCESS_TOKEN_LIFETIME` (15 minute) aur `REFRESH_TOKEN_LIFETIME` (7 din), seconds me
- `REFRESH_TOKEN_IN_COOKIE` (True): refresh token httpOnly cookie me, False ho to response body me
- `REFRESH_TOKEN_ROTATION` (True): har refresh par naya token, purana blacklist
- `REFRESH_COOKIE_NAME`, `REFRESH_COOKIE_PATH`, `REFRESH_COOKIE_SECURE` (None = DEBUG band ho to Secure), `REFRESH_COOKIE_SAMESITE` ("Lax")
- `validate()` me: lifetimes positive int, booleans, samesite ki value, aur `token_blacklist` app `INSTALLED_APPS` me hai ya nahi

### Kaise kaam karta hai

- Access token hamesha response body me. Refresh token ya cookie me ya body me, kabhi dono me nahi
- Package apni `AUTHNEST` lifetimes use karta hai, project ka `SIMPLE_JWT` nahi chhedta (`AuthnestRefreshToken.lifetime` property)
- Login: `authenticate(..., username=identifier, scope=...)`, galat user ya galat password dono par ek hi 401 message
- Email verify check password sahi hone ke baad, aur sirf jab user ke paas email ho (phone-only user bachta hai)
- Refresh: token kholne se signature, expiry aur blacklist check, phir `User.objects` (alive-only) se user, soft-deleted user ka token ruk jata hai
- Logout: refresh token invalid ho tab bhi "logout ho gaya" (user ko log out hi hona tha)
- Teeno views par `authentication_classes = []`, taaki purana access token header me ho to bhi 401 na aaye
- `APIException` use hua, `AuthenticationFailed` nahi, kyunki `authentication_classes = []` par DRF use 401 ki jagah 403 bana deta hai

### Demo me settings

- `INSTALLED_APPS` me `"rest_framework_simplejwt.token_blacklist"`, phir `python manage.py migrate`
- `DEBUG = True` rakho development me, warna cookie `Secure` ban jati hai aur `http://` par Postman use nahi bhejta

### Test kaise kiya (Postman)

- Login ke baad cookie Postman ke cookie jar me save, response body me `refresh` nahi
- `token/refresh/` bina body ke chalta hai (cookie apne aap jati hai), `Authorization` header ki zaroorat nahi
- Purani cookie ki value dobara bhejne par 401 (rotation), logout ke baad refresh par 401
- `REFRESH_TOKEN_IN_COOKIE=False` par `refresh` body me aata hai aur refresh/logout body se chalte hain
- Login aur refresh ka host bilkul same rakho (`localhost` aur `127.0.0.1` alag cookie maane jaate hain)
- Admin aur user scopes alag: normal user `admin/login/` me aur admin `login/` me 401
- Shell me `OutstandingToken` aur `BlacklistedToken` ke counts check kiye

### Errors jo aaye aur fix

- `ModuleNotFoundError: No module named 'rest_framework_simplejwt.token_blacklist'`: venv active hai ya nahi (`where python`), `pip show djangorestframework-simplejwt`, phir `pip install --upgrade --force-reinstall djangorestframework-simplejwt`
- Refresh token Postman se bhejne ke liye cookie mode me kuch daalna nahi padta, body mode me `{"refresh": "..."}`

### Baaki (aage ke steps me)

- CORS aur `withCredentials: true` React side (Step 9) me
- Password change ya soft delete par user ke saare outstanding tokens blacklist karna (Step 5 aur 6)
- 2FA check login view me Step 7 me

## Step 5 ho gaya: Forgot, reset aur change password

### Folder me ye files jude/badle (`authnest/` ke andar)

```
authnest/
|-- serializers.py    (ForgotPasswordSerializer, ResetPasswordSerializer, ChangePasswordSerializer)
|-- views.py          (ForgotPasswordView, ResetPasswordView, ChangePasswordView)
|-- urls.py           (3 naye routes)
+-- services/
|   |-- tokens.py     (password_fingerprint, make/read_password_reset_token, blacklist_all_tokens)
|   +-- emails.py     (send_password_reset_email, send_password_changed_email)
+-- templates/authnest/email/
    |-- password_reset.html / .txt
    +-- password_changed.html / .txt
```

### Endpoints

- `POST /auth/forgot-password/` body `{"email": "..."}`: response hamesha same, email registered ho ya nahi
- `POST /auth/reset-password/` body `{"token": "...", "password": "..."}`: password set, saare refresh tokens blacklist, "password badal gaya" email
- `POST /auth/change-password/` (Bearer access token) body `{"old_password": "...", "new_password": "..."}`: password badalta hai, saare refresh tokens blacklist (current device ka bhi), cookie hat jati hai

### Kaise kaam karta hai

- Reset token me user id ke saath `password_fingerprint` (password hash ka SHA-256 ka 20 characters). Password badalte hi fingerprint badal jata hai, to wahi link dobara kaam nahi karta, alag "used" table ki zaroorat nahi
- Reset link ke expiry `PASSWORD_RESET_TIMEOUT` (`AUTHNEST` ki setting, Django ki built-in nahi)
- Kamzor password par 400 aata hai par token consume nahi hota, kyunki fingerprint tabhi badalta hai jab password save ho
- Reset ke baad auto-login nahi, sirf message
- Password save aur `blacklist_all_tokens` ek `transaction.atomic()` me, email uske baad
- Access token jo pehle mil chuka hai wo apni expiry (15 minute) tak chalta hai, isliye `ACCESS_TOKEN_LIFETIME` chhota rakhna
- Phone-only user (email nahi) ka reset abhi nahi ho sakta, SMS OTP baad ka optional feature
- Rate limiting (throttling) abhi nahi, Step 8 me

### Test kaise kiya

- Reset token shell se banao (`make_password_reset_token(user)`), console se copy karne par quoted-printable ki galti aati hai
- Forgot password registered aur anjaan email dono par same response
- Wahi reset token dobara: 400. Kamzor password par 400 aur token dobara chalta hai
- Reset ya change ke baad `token/refresh/` par 401
- Change password: galat `old_password` 400, naya password purane jaisa 400, bina header 401

### Errors jo aaye aur fix

- Reset token ke baad shell me `set_password` chalane se wahi token invalid ho jata hai (fingerprint badal gaya). Token banane ke baad password mat chhedo
- `SignatureExpired` jaisa error: purani testing wali `PASSWORD_RESET_TIMEOUT` ya `EMAIL_VERIFICATION_TIMEOUT` setting `AUTHNEST` me pad rahi hoti hai

## Step 6A ho gaya: Profile API

### Folder me ye files jude/badle (`authnest/` ke andar)

```
authnest/
|-- conf.py           (PROFILE_PICTURE_MAX_SIZE jodi)
|-- serializers.py    (ProfileSerializer)
|-- views.py          (ProfileView, ProfilePictureView)
+-- urls.py           (2 naye routes)
```

### Endpoints (Bearer access token zaroori)

- `GET /auth/profile/`: apni profile
- `PATCH /auth/profile/`: `first_name`, `last_name`, `dob`, `profile_picture` (multipart form-data ya JSON)
- `DELETE /auth/profile/picture/`: picture hatana, 204

### Kaise kaam karta hai

- `ModelSerializer` me koi field declare nahi, taaki model ki settings (file upload, null allowed, optional) bani rahein. `fields` aur `read_only_fields` ka whitelist: email, phone, verified flags profile se nahi badalte
- `validate_dob` (bhavishya ya 120 saal se purani date par error), `validate_profile_picture` (size `PROFILE_PICTURE_MAX_SIZE` se)
- `update()` me purani picture ko storage se hatate hain (naam se `storage.delete`), `FieldFile.delete()` nahi, kyunki wo instance ka field `None` kar deta hai
- `ProfileView`: `RetrieveUpdateAPIView`, `get_object` me `request.user`, `http_method_names` me `put` nahi, `parser_classes` me `MultiPartParser`
- Views par `authentication_classes = [JWTAuthentication]` khud set, project ke `REST_FRAMEWORK` defaults par depend nahi

### Demo me settings

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

`demo/config/urls.py` me `urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)`. `pillow` install hona chahiye.

### Errors jo aaye aur fix

- `conf.py` ka size check ulta likha tha (`if not isinstance(..., bool)`), jisse sahi value par bhi error aata. Sahi form: bool ya non-int ya 0 se kam par error
- `profile_picture = serializers.CharField()` aur `dob = serializers.DateField()` declare karne se upload aur null band ho gaye. Jab tak default se kuch alag nahi chahiye, field declare mat karo
- Image test me Postman me Body type **form-data** chuno (raw JSON nahi) aur key type **File**

## Step 6B ho gaya: Email change

### Folder me ye files jude/badle (`authnest/` ke andar)

```
authnest/
|-- conf.py           (CONFIRM_EMAIL_CHANGE_PATH jodi)
|-- serializers.py    (EmailChangeSerializer, ConfirmEmailChangeSerializer)
|-- views.py          (EmailChangeView, ConfirmEmailChangeView)
|-- urls.py           (2 naye routes)
+-- services/
|   |-- tokens.py     (make/read_email_change_token)
|   +-- emails.py     (send_email_change_email, send_email_changed_notice)
+-- templates/authnest/email/
    |-- email_change.html / .txt
    +-- email_changed_notice.html / .txt
```

### Endpoints

- `POST /auth/email/change/` (Bearer access token) body `{"new_email": "...", "password": "..."}`: password sahi ho to **nayi email par** confirm link jata hai, purani email tab tak chalti rahti hai
- `POST /auth/email/change/confirm/` body `{"token": "..."}`: email badalti hai, `is_email_verified=True`, aur **purani email par notice** jata hai. Login zaroori nahi (link kisi bhi device par khul sakta hai)

### Kaise kaam karta hai

- Token me `uid`, `old` aur `new` email. Confirm ke waqt `user.email == payload["old"]` dekhte hain, to email badalte hi wahi link dobara kaam nahi karta
- Phone-only user (email `None`) isi se email jod sakta hai, notice tab nahi jata (purani email nahi)
- Password maangna zaroori: email login ka identifier hai, access token chori ho to bina password ke account hijack ho sakta tha
- Duplicate check `all_objects` se (soft-deleted ki email bhi reserved), aur confirm me dobara (request aur confirm ke beech koi aur le sakta hai), `IntegrityError` bhi pakda
- Email bhejna fail ho to 503 (user ko batana zaroori), notice fail ho to sirf log
- Email badalne par tokens blacklist nahi hote (JWT me user id hai, email nahi)
- Expiry `EMAIL_VERIFICATION_TIMEOUT` hi use hoti hai, alag setting nahi

### Test kaise kiya

- Token shell se: `make_email_change_token(user, "naya@x.com")`
- Galat password, apni hi email, kisi aur ki email: 400. Sahi request: 200, email `naya@x.com` ke naam se print, shell me email abhi purani
- Confirm: 200, email badli, purani email ke naam se notice print. Wahi token dobara 400
- Naye email se login chalta hai, purani se 401
- Phone-only user email jod sakta hai
- `PATCH /auth/profile/` se email ab bhi nahi badalti

## Step 6C ho gaya: Account delete

### Folder me ye files jude/badle (`authnest/` ke andar)

```
authnest/
|-- serializers.py    (DeleteAccountSerializer)
|-- views.py          (DeleteAccountView)
|-- urls.py           (1 naya route)
+-- services/emails.py  (send_account_deleted_email)
+-- templates/authnest/email/account_deleted.html / .txt
```

### Endpoint

- `POST /auth/account/delete/` (Bearer access token) body `{"password": "..."}`. `DELETE` ki jagah `POST`, kyunki password body me jana chahiye aur DELETE ki body har client/proxy par bharosemand nahi

### Kaise kaam karta hai

- Password sahi ho to `blacklist_all_tokens(user)` aur `user.delete()` ek `transaction.atomic()` me
- `user.delete()` model ka apna `delete()` hai jo `SOFT_DELETE` setting se tay karta hai (soft ya hard), view me `if` nahi
- Last active superuser apna account delete nahi kar sakta (400)
- Email save karke rakhte hain (hard delete ke baad user par bharosa nahi), email transaction ke baad jata hai
- Delete ke turant baad purana access token bhi kaam nahi karta, kyunki simplejwt user ko `objects` (alive-only) se dhundhta hai
- Soft delete me email/phone reserved rehte hain (dobara register par "pehle se maujood hai"), restore shell se: `User.all_objects.filter(pk=...).restore()`
- Social auth wale user ka password nahi hoga, wahan alag confirmation tareeka chahiye

### Test kaise kiya

- Alag test user banake delete kiya: galat password 400, sahi 200, email print, cookie hat gayi
- Delete ke baad: profile 401, refresh 401, login 401
- Shell me `User.objects` me nahi, `User.all_objects` me hai, `deleted_at` bhara, `is_active=False`
- Wahi email se register 400, restore ke baad login 200
- Last superuser 400, doosra superuser banane ke baad chalta hai
- `SOFT_DELETE=False` par row hat jati hai aur email dobara register ho sakti hai

## Aage ke steps (order)

- Step 1: `conf.py` aur `apps.py` ho gaya
- Step 2: User model + custom auth backend ho gaya
- Step 3: Register + email verification ho gaya
- Step 4: Login + JWT + refresh/logout ho gaya
- Step 5: Forgot/reset/change password + email templates ho gaya
- Step 6: Profile APIs ho gaya (6A profile, 6B email change, 6C account delete)
- Step 7: 2FA
- Step 8: Tests
- Step 9: React side
