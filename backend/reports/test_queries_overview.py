from django.core.cache import cache
from django.urls import reverse

from nanopore.test_access import AccessTestBase
from utils import access


class QueriesOverviewTests(AccessTestBase):
    def setUp(self):
        cache.clear()

    def test_total_matches_sidebar_and_follows_role(self):
        admin = self.make_user("admin", [access.ADMIN])
        self.client.force_login(admin)
        page = self.client.get(reverse("reports:all_queries_overview"))
        self.assertEqual(page.context["grand_total"], page.context["context_total_issues"])
        self.assertEqual({f["key"] for f in page.context["forms"]}, set(access.ALL_FORMS))
        # A zone filter counts only that zone
        zone = self.client.get(reverse("reports:all_queries_overview"), {"zone": self.zone_b.pk})
        self.assertLessEqual(zone.context["grand_total"], page.context["grand_total"])

        lab = self.make_user("lab", [access.LABORATORY_TECHNICIAN], zones=[self.zone_a])
        self.client.force_login(lab)
        page = self.client.get(reverse("reports:all_queries_overview"))
        self.assertEqual({f["key"] for f in page.context["forms"]}, {access.ZONAL_LAB, access.EDCS_TBLIS})
        self.assertEqual(page.context["grand_total"], page.context["context_total_issues"])

    def test_query_pages_open(self):
        self.client.force_login(self.make_user("admin", [access.ADMIN]))
        names = ["missing_form_queries", "specific_form_queries", "screening_quality_report", "enrollment_quality_report",
                 "clinic_quality_report", "diagnosis_quality_report", "regimen_quality_report", "zonal_quality_report",
                 "edcs_tblis_quality_report"]
        for name in names:
            self.assertEqual(self.client.get(reverse(f"reports:{name}"), {"zone": self.zone_a.pk}).status_code, 200, name)
        for form_type in access.MISSING_FORM_TYPES:
            url = reverse("reports:missing_form_details_queries", args=[form_type])
            self.assertEqual(self.client.get(url).status_code, 200, form_type)
