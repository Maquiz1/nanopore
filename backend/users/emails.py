"""Account emails and passwords: the activation link sent when an account is created (or resent),
the password-reset link an admin can send, and generated passwords.

The link opens a page where the person chooses their own password; that also
activates the account. No password is ever sent by email. The link works once
(choosing a password invalidates it) and expires after PASSWORD_RESET_TIMEOUT.
"""
import secrets
from urllib.parse import urlsplit

from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from notifications.mail import absolute_url, send_email, site_url

ACTIVATION = "account_activation"
PASSWORD_RESET = "password_reset"
# No 0/O, 1/l/I: easy to read out or type from a screen
PASSWORD_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"


def random_password(length=12):
    return "".join(secrets.choice(PASSWORD_CHARS) for _ in range(length))


def activation_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return absolute_url(reverse("users:activate_account", kwargs={"uidb64": uid, "token": token}))


def send_activation_email(user):
    """Email the activation link. Returns False when the user has no email or sending failed."""
    if not user.email:
        return False
    return send_email(
        user.email, "Activate your DREAM Nanopore account", "emails/account_activation",
        {"user": user, "name": user.get_full_name() or user.username, "username": user.username,
         "activation_url": activation_url(user), "login_url": absolute_url(reverse("users:login"))},
        ACTIVATION,
    )


def send_password_reset_email(user):
    """Email a link to choose a new password (the same email as "Forgot password")."""
    if not user.email:
        return False
    url = urlsplit(site_url())
    return send_email(
        user.email, "Reset your DREAM Nanopore password", "registration/password_reset_email",
        {"user": user, "protocol": url.scheme, "domain": url.netloc,
         "uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": default_token_generator.make_token(user)},
        PASSWORD_RESET,
    )
