"""Dashboard shows each role the sections its forms allow."""
from django.urls import reverse
from nanopore.test_access import AccessTestBase
from utils import access

class DashboardSectionsTests(AccessTestBase):
    def test_each_role_sees_the_right_sections(self):
        cases = [
            ([access.NURSE], True, False), ([access.LABORATORY_TECHNICIAN], False, True),
            ([access.DATA_SPECIALIST], True, True), ([access.STATISTICIAN], True, True),
            ([access.REVIEWER], True, True), ([access.ADMIN], True, True),
        ]
        for roles, clinical, lab in cases:
            user = self.make_user("u_" + roles[0].lower(), roles, sites=[self.a1])
            self.client.force_login(user)
            html = self.client.get(reverse("dashboard:dashboard")).content.decode()
            self.assertEqual("Enrollment against targets" in html, clinical, roles)
            self.assertEqual("Zonal laboratory pipeline" in html, lab, roles)
