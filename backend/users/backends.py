from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameOrEmailBackend(ModelBackend):
    """Log in with the username or the email address (email only when it belongs to one account)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        username = username.strip()
        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if user is None and "@" in username:
            matches = list(User.objects.filter(email__iexact=username)[:2])
            user = matches[0] if len(matches) == 1 else None
        if user is None:
            User().set_password(password)  # same work as a real check, so timing doesn't reveal accounts
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
