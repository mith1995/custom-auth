from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string 

from ..conf import authnest_settings
from .tokens import (
    make_email_verification_token, 
    make_password_reset_token, 
    make_email_change_token
)

def build_frontend_url(path, **params):
    base = authnest_settings.FRONTEND_URL.rstrip("/")
    path = "/" + path.lstrip("/")
    return f"{base}{path}?{urlencode(params)}"

def send_templated_email(subject, to_email, template, context):
    html_body = render_to_string(f"authnest/email/{template}.html", context)
    text_body = render_to_string(f"authnest/email/{template}.txt", context)

    message = EmailMultiAlternatives(
        subject, text_body, settings.DEFAULT_FROM_EMAIL, [to_email]
    )
    message.attach_alternative(html_body, "text/html")
    message.send()

def send_verification_email(user):
    token = make_email_verification_token(user)
    link = build_frontend_url(authnest_settings.VERIFY_EMAIL_PATH, token=token)
    send_templated_email(
        subject = "Please verify your email address.",
        to_email = user.email,
        template = "verify_email",
        context = {
            "user": user,
            "link": link,
            "expires_in_hours": authnest_settings.EMAIL_VERIFICATION_TIMEOUT // 3600
        }
    )

def send_password_reset_email(user):
    token = make_password_reset_token(user)
    link = build_frontend_url(authnest_settings.RESET_PASSWORD_PATH, token=token)
    send_templated_email(
        subject="Reset your password.",
        to_email=user.email,
        template="password_reset",
        context={
            "user": user,
            "link": link,
            "expires_in_minutes": authnest_settings.PASSWORD_RESET_TIMEOUT // 60,
        },
    )


def send_password_changed_email(user):
    if not user.email:
        return  # Emails are not sent to phone-only users.
    send_templated_email(
        subject="Your password has been changed successfully.",
        to_email=user.email,
        template="password_changed",
        context={"user": user},
    )

def send_email_change_email(user, new_email):
    token = make_email_change_token(user, new_email)
    link = build_frontend_url(authnest_settings.CONFIRM_EMAIL_CHANGE_PATH, token=token)
    send_templated_email(
        subject="Confirm your new email address.",
        to_email=new_email,
        template="email_change",
        context={
            "user": user,
            "new_email": new_email,
            "link": link,
            "expires_in_hours": authnest_settings.EMAIL_VERIFICATION_TIMEOUT // 3600,
        },
    )


def send_email_changed_notice(user, old_email, new_email):
    send_templated_email(
        subject="Your email address has been changed successfully.",
        to_email=old_email,
        template="email_changed_notice",
        context={"user": user, "old_email": old_email, "new_email": new_email},
    )

def send_account_deleted_email(user, to_email):
    send_templated_email(
        subject="Your account has been deleted successfully.",
        to_email=to_email,
        template="account_deleted",
        context={"user": user, "permanent": not authnest_settings.SOFT_DELETE},
    )