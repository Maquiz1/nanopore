"""
Sending system emails. Every email goes through `send_email`, which renders the
text and HTML templates, uses the sender and site address from SiteConfiguration,
and writes one EmailLog row per recipient (sent or failed).
"""
import logging
from email.utils import formataddr, parseaddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import EmailLog, EmailRecipient, SiteConfiguration

logger = logging.getLogger(__name__)


def emails_enabled():
    """EMAILS_ENABLED in settings (.env). Off: nothing is sent and nothing is logged."""
    return bool(getattr(settings, "EMAILS_ENABLED", False))


def _config():
    return SiteConfiguration.objects.filter(is_active=True).first()


def site_url():
    """Base address used in email links, without a trailing slash."""
    config = _config()
    url = config.site_url if config else getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    return url.rstrip("/")


def absolute_url(path):
    return site_url() + path


def from_email():
    """Sender: SiteConfiguration's name/address, falling back to DEFAULT_FROM_EMAIL."""
    default_name, default_email = parseaddr(settings.DEFAULT_FROM_EMAIL)
    config = _config()
    name = (config and config.from_name) or default_name
    email = (config and config.from_email) or default_email
    return formataddr((name, email)) if name else email


def report_copies():
    """(to, bcc) of the extra recipients set under Administration > Email recipients.
    They receive the all-sites copy of each weekly email: CC people see each other, BCC people don't."""
    to, bcc = [], []
    for r in EmailRecipient.objects.filter(is_active=True):
        (to if r.type == EmailRecipient.CC else bcc).append(r.email)
    return to, bcc


def already_sent(recipient, subject, task_type):
    """True when this email already reached this person (a re-run task must not send it twice)."""
    return EmailLog.objects.filter(recipient=recipient, subject=subject, task_type=task_type,
                                   status=EmailLog.SENT).exists()


def send_email(to, subject, template, context, task_type, bcc=()):
    """Send `template`.txt and `template`.html to one address or a list. Returns True when sent.
    One EmailLog row is written per address. Returns False without sending while emails are off."""
    if not emails_enabled():
        return False
    to = [to] if isinstance(to, str) else list(to)
    bcc = [e for e in bcc if e not in to]
    if not to and bcc:
        to, bcc = bcc[:1], bcc[1:]
    context = {"site_url": site_url(), **context}
    try:
        message = EmailMultiAlternatives(
            subject, render_to_string(f"{template}.txt", context), from_email(), to, bcc=bcc,
        )
        message.attach_alternative(render_to_string(f"{template}.html", context), "text/html")
        message.send()
        status, error = EmailLog.SENT, ""
    except Exception as e:  # SMTP down, bad address...: log it and carry on with the others
        logger.error("%s email to %s failed: %s", task_type, ", ".join(to), e, exc_info=True)
        status, error = EmailLog.FAILED, str(e)
    EmailLog.objects.bulk_create([
        EmailLog(recipient=address, subject=subject, task_type=task_type, status=status, error_message=error)
        for address in to + bcc
    ])
    return status == EmailLog.SENT
