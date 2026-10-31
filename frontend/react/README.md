# Flowspace — React + Tailwind Authentication Starter

A responsive SaaS-style custom authentication UI built with React, Vite, Tailwind CSS, React Router, Lucide icons, and react-hot-toast.

## Pages
- `/signin` — Sign in with email/password validation and password visibility toggle
- `/register` — Registration with name/email/password/confirm password and terms validation
- `/dashboard` — Responsive protected dashboard with sidebar, stat cards, projects, activity, search, and sign out
- `/forgot-password` — Email validation and reset-request confirmation state
- `/reset-password` — New password + confirmation validation

## Run locally
Requires Node.js 18+.

```bash
npm install
npm run dev
```

Open the local URL Vite prints, usually `http://localhost:5173`.

Production build:

```bash
npm run build
npm run preview
```

## Demo authentication warning
This project is a **UI starter**, not production-ready authentication:
- It uses `localStorage` to simulate a signed-in user.
- Sign-in accepts any valid email and non-empty password. Registration stores only a demo name/email.
- Forgot/reset password screens show demo success states; no email is sent and no password is changed.
- Google sign-in is a placeholder.
- Do not use this demo logic to protect real user data.

## Connect a real backend
Replace the functions in `src/context/AuthContext.jsx` with API calls to your backend:
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `POST /api/auth/password-reset/`
- `POST /api/auth/password-reset/confirm/`

Recommended production approach:
- Use HTTPS.
- Prefer `HttpOnly`, `Secure`, `SameSite` cookies for session/refresh tokens where practical.
- Validate credentials, authorization, reset tokens, expiry, and rate limits on the server.
- Never store raw passwords in browser storage.
- Use generic forgot-password responses to avoid revealing whether an email exists.
- Add CSRF protection when cookie-based auth requires it.
- Keep secrets in environment variables on the server, never in frontend code.

## Project structure
```text
src/
  components/
    AuthLayout.jsx
    Brand.jsx
    FormField.jsx
    PrimaryButton.jsx
    StatCard.jsx
  context/
    AuthContext.jsx
  lib/
    validation.js
  pages/
    SignIn.jsx
    Register.jsx
    Dashboard.jsx
    ForgotPassword.jsx
    ResetPassword.jsx
  App.jsx
  index.css
  main.jsx
```
