"""Every page needs a login, except the few public ones (login, sign-up, password reset)."""
import re

from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver

PUBLIC_PAGES = {
    "users:login", "users:sign_up", "users:resend_activation", "users:session_expired",
    "users:password_reset", "users:password_reset_done", "users:password_reset_confirm",
    "users:password_reset_complete", "users:activate_account", "users:logout",
    ":root_redirect",
}


def _walk(patterns, prefix="", namespace=""):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from _walk(pattern.url_patterns, prefix + str(pattern.pattern), pattern.namespace or namespace)
        elif isinstance(pattern, URLPattern):
            yield prefix + str(pattern.pattern), f"{namespace}:{pattern.name}"


def _example_url(route):
    route = route.lstrip("^").rstrip("$")
    route = re.sub(r"<int:\w+>", "1", route)
    route = re.sub(r"<(?:str:|slug:|path:)?\w+>", "x", route)
    return "/" + route.replace("\\", "")


class PublicPagesTests(TestCase):
    def test_only_public_pages_open_without_login(self):
        open_pages = []
        for route, name in _walk(get_resolver().url_patterns):
            if route.startswith(("admin/", "static/", "media/")) or "(?P" in route or name in PUBLIC_PAGES:
                continue
            url = _example_url(route)
            try:
                status = self.client.get(url).status_code
            except Exception:  # a page that crashes for anonymous users still must not render
                status = 500
            if status not in (301, 302, 403, 404, 405):
                open_pages.append(f"{name} {url} -> {status}")
        self.assertEqual(open_pages, [], "these pages open without login")


class StaffPagesTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from users.models import Profile
        self.admin = User.objects.create_user("admin", password="pw", is_superuser=True, is_staff=True)
        self.nurse = User.objects.create_user("nurse", password="pw")
        self.other = User.objects.create_user("other", password="pw")
        for user in (self.admin, self.nurse, self.other):
            Profile.objects.create(user=user)

    def test_staff_list_and_edit_are_superuser_only(self):
        from django.urls import reverse
        self.client.force_login(self.nurse)
        self.assertEqual(self.client.get(reverse("users:staff_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("users:staff_update", args=[self.other.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("users:staff_update", args=[self.other.pk]), {}).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("users:staff_list")).status_code, 200)

    def test_profile_is_own_or_superuser(self):
        from django.urls import reverse
        self.client.force_login(self.nurse)
        self.assertEqual(self.client.get(reverse("users:staff_detail", args=[self.nurse.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("users:staff_detail", args=[self.other.pk])).status_code, 403)
