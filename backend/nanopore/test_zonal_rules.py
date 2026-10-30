"""Dar es Salaam Zonal Lab: lab number only (nanopore/zonal_rules.py)."""
from datetime import date

from django.urls import reverse

from locations.models import District, Region, Site, SiteLevel, Zone
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.models import EdcsTblisZonal, Screening, ZonalLaboratory
from nanopore.tasks_tblis_raw import sync_zonal_laboratory_to_edcs
from options.models import FirstLineDrugs, YesNo
from nanopore.test_access import AccessTestBase
from reports.services.zonal_dq import get_zonal_counts, get_zonal_dq
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

    def test_dar_form_asks_only_what_tblis_cannot_supply(self):
        form = ZonalLaboratoryForm(screening_instance=self.dar_screening)
        self.assertTrue(form.lab_number_only)
        self.assertLessEqual({"screening", "unique_lab_no", "remarks", "nanopore_done", "nanopore_results",
                              "epi_to_me", "sequencing_delayed", "nano_rifampicin"}, set(form.fields))
        for name in ("culture_performed", "lpa", "first_line_lpa", "lpa1_mtb", "rifampicin", "isolate_unique_lab_no",
                     "first_line_drugs", "second_line_drugs"):
            self.assertNotIn(name, form.fields)
        self.assertFalse(form.fields["nanopore_done"].required)

    def test_dar_checkboxes_open_only_for_lpa_lines_tblis_says_were_done(self):
        yes = YesNo.objects.get(pk=1)
        no = YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})[0]
        edcs = EdcsTblisZonal.objects.create(screening=self.dar_screening, unique_lab_no="CTRL-5", first_line_lpa=yes, second_line_lpa=no)
        form = ZonalLaboratoryForm(screening_instance=self.dar_screening)
        self.assertIn("first_line_drugs", form.fields)
        self.assertNotIn("second_line_drugs", form.fields)
        edcs.first_line_lpa, edcs.second_line_lpa = no, yes
        edcs.save()
        form = ZonalLaboratoryForm(screening_instance=self.dar_screening)
        self.assertNotIn("first_line_drugs", form.fields)
        self.assertIn("second_line_drugs", form.fields)

    def test_sync_carries_ctrl_entries_to_edcs_and_keeps_tblis_values_apart(self):
        yes = YesNo.objects.get(pk=1)
        band = FirstLineDrugs.objects.create(name="rpoB", value=1)
        EdcsTblisZonal.objects.create(screening=self.dar_screening, unique_lab_no="CTRL-6", first_line_lpa=yes)
        admin = self.make_user("admin_dar", [access.ADMIN])
        self.client.force_login(admin)
        url = reverse("nanopore:zonal-laboratory-create") + f"?screening={self.dar_screening.pk}"
        self.client.post(url, {"screening": self.dar_screening.pk, "unique_lab_no": "CTRL-6", "remarks": "Seen",
                               "nanopore_done": yes.pk, "first_line_drugs": [band.pk]})
        lab = ZonalLaboratory.objects.get(screening=self.dar_screening)
        self.assertEqual((lab.remarks, lab.nanopore_done), ("Seen", yes))
        self.assertEqual(list(lab.first_line_drugs.all()), [band])
        edcs = sync_zonal_laboratory_to_edcs(lab)
        self.assertEqual((edcs.remarks, edcs.nanopore_done), ("Seen", yes))
        self.assertEqual(list(edcs.first_line_drugs.all()), [band])

    def test_edcs_record_is_read_only(self):
        lab = ZonalLaboratory.objects.create(screening=self.dar_screening, unique_lab_no="CTRL-8")
        edcs = EdcsTblisZonal.objects.create(screening=self.dar_screening, unique_lab_no="CTRL-8", remarks="Old")
        admin = self.make_user("admin_read", [access.ADMIN])
        self.client.force_login(admin)
        for name in ("nanopore:edcs-tblis-laboratory-view", "nanopore:edcs-tblis-laboratory-update"):
            url = reverse(name, args=[edcs.pk])
            page = self.client.get(url)
            self.assertContains(page, "Read only.")
            self.assertContains(page, reverse("nanopore:zonal-laboratory-update", args=[lab.pk]))
            self.assertTrue(all(field.disabled for field in page.context["form"].fields.values()))
            self.assertNotContains(page, 'type="submit"')
            self.assertEqual(self.client.post(url, {"unique_lab_no": "CTRL-8", "remarks": "New"}).status_code, 405)
        edcs.refresh_from_db()
        self.assertEqual(edcs.remarks, "Old")
        self.client.force_login(self.make_user("stat_read", [access.STATISTICIAN], zones=[self.zone_a]))
        self.assertEqual(self.client.get(reverse("nanopore:edcs-tblis-laboratory-view", args=[edcs.pk])).status_code, 404)

    def test_culture_isolate_is_not_queried_for_dar(self):
        admin = self.make_user("admin_iso", [access.ADMIN])
        self.assertNotIn("missing_culture_isolate", get_zonal_counts(admin, EdcsTblisZonal)[0])
        self.assertIn("missing_culture_isolate", get_zonal_counts(admin, ZonalLaboratory)[0])

    def test_edcs_query_pids_open_the_zonal_lab_form(self):
        lab = ZonalLaboratory.objects.create(screening=self.dar_screening, unique_lab_no="CTRL-7")
        EdcsTblisZonal.objects.create(screening=self.dar_screening, unique_lab_no="CTRL-7")
        self.client.force_login(self.make_user("admin_link", [access.ADMIN]))
        page = self.client.get(reverse("reports:edcs_tblis_quality_report"))
        self.assertContains(page, reverse("nanopore:zonal-laboratory-update", args=[lab.pk]))
        self.assertNotContains(page, "/edcs-tblis/edcs-tblis-laboratory/form")

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
        self.assertContains(page, "enter the <strong>Unique Lab Number</strong> and Remarks", html=False)

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
