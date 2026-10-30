from datetime import date

from django.core.cache import cache
from django.urls import reverse

from locations.models import District, Region, Site, Zone
from nanopore.models import EdcsTblisZonal, Screening, ZonalLaboratory
from options.models import YesNoNA
from nanopore.test_access import AccessTestBase
from reports.services.zonal_dq import serialize_record
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


class LabQueryColumnsTests(AccessTestBase):
    def setUp(self):
        cache.clear()
        self.client.force_login(self.make_user("admin_cols", [access.ADMIN]))

    def test_isolate_number_follows_question_11(self):
        lab = self.zonal_labs["A1"]
        yes, _ = YesNoNA.objects.get_or_create(pk=1, defaults={"name": "Yes", "value": 1})
        no, _ = YesNoNA.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})

        self.assertEqual(serialize_record(lab, [])["isolate_no"], "Not answered")
        lab.culture_isolate = no
        self.assertEqual(serialize_record(lab, [])["isolate_no"], "N/A")
        lab.culture_isolate = yes
        self.assertEqual(serialize_record(lab, [])["isolate_no"], "Not entered")
        lab.isolate_unique_lab_no = "ISO-1"
        self.assertEqual(serialize_record(lab, [])["isolate_no"], "ISO-1")
        self.assertEqual(serialize_record(lab, [])["lab_no"], "LAB-A1")

    def test_query_lists_show_both_columns(self):
        yes, _ = YesNoNA.objects.get_or_create(pk=1, defaults={"name": "Yes", "value": 1})
        ZonalLaboratory.objects.filter(pk=self.zonal_labs["A1"].pk).update(culture_performed=None, culture_isolate=yes)
        page = self.client.get(reverse("reports:zonal_quality_report"))
        self.assertContains(page, "<th>Isolate Lab No.</th>")
        self.assertContains(page, "<td>LAB-A1</td>")
        self.assertContains(page, "<td>Not entered</td>")

        # The EDCS/TBLIS page lists Dar es Salaam only (reports/services/zonal_dq/queryset.py)
        dar = Zone.objects.create(name="Dar es salaam", country=self.zone_a.country)
        region = Region.objects.create(name="Dar region", country=self.zone_a.country, zone=dar)
        district = District.objects.create(name="Temeke", region=region)
        site = Site.objects.create(name="Temeke Hospital", district=district, pid_prefix="DM-", site_level=self.a1.site_level)
        screening = Screening.objects.create(screening_date=date(2025, 3, 1), pid1="001", pid2="001", site=site, eligible=True)
        EdcsTblisZonal.objects.create(screening=screening, unique_lab_no="DAR-1", culture_isolate=yes)
        cache.clear()
        page = self.client.get(reverse("reports:edcs_tblis_quality_report"))
        self.assertContains(page, "<th>Isolate Lab No.</th>")
        self.assertContains(page, "<td>DAR-1</td>")
        self.assertContains(page, "<td>Not entered</td>")
