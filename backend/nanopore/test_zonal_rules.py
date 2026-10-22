"""Dar es Salaam Zonal Lab: lab number only (nanopore/zonal_rules.py)."""
from datetime import date

from django.urls import reverse

from locations.models import District, Region, Site, SiteLevel, Zone
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.models import Screening, ZonalLaboratory
from nanopore.test_access import AccessTestBase
from reports.services.zonal_dq import get_zonal_dq
from utils import access


class DarEsSalaamZonalLabTests(AccessTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        country = cls.zone_a.country
        dar = Zone.objects.create(name="Dar es salaam", country=country)
        region = Region.objects.create(name="Dar region", country=country, zone=dar)
        district = District.objects.create(name="Temeke", region=region)
        site = Site.objects.create(
            name="Temeke Hospital", district=district, pid_prefix="DF_TZ_SS2_18_",
            site_level=SiteLevel.objects.get(code="local"),
        )
        cls.dar_screening = Screening.objects.create(
            screening_date=date(2025, 3, 1), pid1="002", pid2="002", site=site, eligible=True,
        )

    def test_dar_form_only_asks_for_lab_number(self):
        form = ZonalLaboratoryForm(screening_instance=self.dar_screening)
        self.assertTrue(form.lab_number_only)
        self.assertEqual(set(form.fields), {"screening", "unique_lab_no"})

    def test_other_zones_keep_the_full_form(self):
        form = ZonalLaboratoryForm(screening_instance=self.screenings["A1"])
        self.assertFalse(form.lab_number_only)
        self.assertTrue(form.fields["culture_performed"].required)
        self.assertTrue(form.fields["date_sputum_received"].required)

    def test_dar_zonal_lab_saved_with_lab_number_only(self):
        admin = self.make_user("admin", [access.ADMIN])
        self.client.force_login(admin)
        url = reverse("nanopore:zonal-laboratory-create") + f"?screening={self.dar_screening.pk}"
        page = self.client.get(url)
        self.assertContains(page, "enter only the <strong>Unique Lab Number</strong>", html=False)

        self.client.post(url, {"screening": self.dar_screening.pk, "unique_lab_no": "CTRL-0001"})
        lab = ZonalLaboratory.objects.get(screening=self.dar_screening)
        self.assertEqual(lab.unique_lab_no, "CTRL-0001")
        self.assertIsNone(lab.culture_performed)

    def test_dar_zonal_lab_still_needs_a_lab_number(self):
        form = ZonalLaboratoryForm(
            data={"screening": self.dar_screening.pk, "unique_lab_no": ""}, screening_instance=self.dar_screening,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("unique_lab_no", form.errors)

    def test_zonal_queries_skip_dar_results_but_not_lab_number(self):
        ZonalLaboratory.objects.create(screening=self.dar_screening, unique_lab_no="CTRL-0002")
        admin = self.make_user("admin", [access.ADMIN])
        _, stats, _, _ = get_zonal_dq(admin, ZonalLaboratory)
        # The A1/A2/B1 fixtures have no culture either; only they are counted.
        self.assertEqual(stats["missing_date_sputum_received"], 3)
        dar_only = ZonalLaboratory.objects.filter(screening=self.dar_screening)
        dar_only.update(unique_lab_no="")
        _, stats, _, _ = get_zonal_dq(admin, ZonalLaboratory)
        self.assertEqual(stats["missing_unique_lab_no"], 1)
