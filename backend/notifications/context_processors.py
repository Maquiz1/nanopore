from notifications.mail import emails_enabled


def emails(request):
    """{{ emails_enabled }}: hide email-only options (reset links, forgot password) while emails are off."""
    return {"emails_enabled": emails_enabled()}
