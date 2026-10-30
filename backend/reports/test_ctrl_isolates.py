"""Other zones' isolate numbers and phenotypic DST are entered and followed up at CTRL."""
from datetime import date

from django.core.cache import cache
from django.urls import reverse

from locations.models import District, Region, Site, SiteLevel, Zone
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.models import EdcsTblisZonal, Screening, TblisRawData, TblisUploadBatch, ZonalLaboratory
from nanopore.test_access import AccessTestBase
from nanopore.zonal_rules import CTRL_FIELDS
from options.models import YesNo, YesNoNA
from reports.models import QueryCount
from reports.services.query_snapshot import take_snapshot
from reports.services.zonal_dq import get_ctrl_isolate_counts, get_zonal_counts, get_zonal_dq
from utils import access

PAGE = "reports:ctrl_isolates"


class CtrlIsolatesTests(AccessTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.isolate_yes = YesNoNA.objects.create(pk=1, name="Yes", value=1)
        cls.isolate_no = YesNoNA.objects.create(pk=2, name="No", value=2)
        country = cls.zone_a.country
        dar = Zone.objects.create(name="Dar es salaam", country=country)
        region = Region.objects.create(name="Dar region", country=country, zone=dar)
        district = District.objects.create(name="Temeke", region=region)
        zonal = SiteLevel.objects.get(code="zonal")
        cls.ctrl = Site.objects.create(name="CTRL Laboratory", district=district, pid_prefix="CT-", site_level=zonal)
        cls.dar_site = Site.objects.create(name="Temeke Hospital", district=district, pid_prefix="DM-",
                                           site_level=SiteLevel.objects.get(code="local"))
        cls.dar_screening = Screening.objects.create(
            screening_date=date(2025, 3, 1), pid1="009", pid2="009", site=cls.dar_site, eligible=True,
        )
        cls.dar_lab = ZonalLaboratory.objects.create(screening=cls.dar_screening, unique_lab_no="DAR-1", culture_isolate=cls.isolate_yes)
        cls.b_lab = cls.zonal_labs["B1"]
        ZonalLaboratory.objects.filter(pk=cls.b_lab.pk).update(culture_isolate=cls.isolate_yes)

    def setUp(self):
        cache.clear()
        self.ctrl_tech = self.make_user("ctrl_tech", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl])
        self.zone_b_tech = self.make_user("b_tech", [access.LABORATORY_TECHNICIAN], zones=[self.zone_b])

    def form_url(self, lab=None):
        return reverse("nanopore:ctrl-isolate-update", args=[(lab or self.b_lab).pk])

    def test_ctrl_technician_covers_other_zones_only_for_this_page(self):
        self.assertTrue(access.is_ctrl_lab(self.ctrl_tech))
        self.assertFalse(access.is_ctrl_lab(self.zone_b_tech))
        self.assertFalse(access.is_ctrl_lab(self.make_user("ctrl_nurse", [access.NURSE], sites=[self.ctrl])))
        self.client.force_login(self.ctrl_tech)
        page = self.client.get(reverse(PAGE))
        self.assertContains(page, self.pid("B1"))
        self.assertNotContains(page, self.dar_screening.pid)  # Dar results come through TB-LIS
        # Their other pages still follow their assignment
        self.assertNotIn(self.pid("B1"), self.visible_pids(self.ctrl_tech))
        self.assertEqual(self.client.get(reverse("nanopore:zonal-laboratory-update", args=[self.b_lab.pk])).status_code, 404)

    def test_zonal_lab_no_longer_gets_ctrl_queries(self):
        stats, total = get_zonal_counts(self.zone_b_tech, ZonalLaboratory)
        self.assertNotIn("missing_isolate_unique_lab_no", stats)
        self.assertNotIn("missing_phenotypic_performed", stats)
        self.client.force_login(self.zone_b_tech)
        page = self.client.get(reverse("reports:zonal_quality_report"))
        self.assertContains(page, "comes from the TB-LIS upload")
        self.assertNotContains(page, reverse(PAGE))
        self.assertEqual(page.context["context_ctrl_isolates_report_total"], 0)
        self.assertEqual(self.client.get(reverse(PAGE)).status_code, 403)
        self.assertEqual(self.client.get(self.form_url()).status_code, 403)

    def test_each_query_is_counted_once(self):
        EdcsTblisZonal.objects.create(screening=self.screenings["B1"], unique_lab_no="LAB-B1", culture_isolate=self.isolate_yes)
        EdcsTblisZonal.objects.create(screening=self.dar_screening, unique_lab_no="DAR-1", culture_isolate=self.isolate_yes)
        admin = self.make_user("admin_once", [access.ADMIN])
        self.assertEqual(get_ctrl_isolate_counts(admin)["missing_isolate_unique_lab_no"], 1)  # B1, not Dar
        self.assertNotIn("missing_isolate_unique_lab_no", get_zonal_counts(admin, ZonalLaboratory)[0])
        self.assertEqual(get_zonal_counts(admin, EdcsTblisZonal)[0]["missing_isolate_unique_lab_no"], 1)  # Dar only

    def test_edcs_page_only_counts_dar(self):
        EdcsTblisZonal.objects.create(screening=self.screenings["B1"], unique_lab_no="LAB-B1")
        EdcsTblisZonal.objects.create(screening=self.dar_screening, unique_lab_no="DAR-1")
        admin = self.make_user("admin_dar", [access.ADMIN])
        qs, stats, total, lists = get_zonal_dq(admin, EdcsTblisZonal)
        self.assertEqual({lab.screening_id for lab in qs}, {self.dar_screening.pk})
        self.assertEqual(sum(stats.values()), total)
        self.assertGreater(stats["missing_culture_performed"], 0)
        self.assertEqual({row["pid"] for row in lists["missing_culture_performed"]}, {self.dar_screening.pid})
        # B1's own problem is still on Zonal Lab
        self.assertGreater(get_zonal_counts(admin, ZonalLaboratory)[1], 0)
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse("reports:edcs_tblis_quality_report")), "Dar es Salaam records only")

    def test_totals_agree_across_sidebar_overview_and_trends(self):
        admin = self.make_user("admin_totals", [access.ADMIN])
        self.client.force_login(admin)
        page = self.client.get(reverse("reports:all_queries_overview"))
        total = sum(get_ctrl_isolate_counts(admin).values())
        self.assertGreater(total, 0)
        self.assertEqual(page.context["context_ctrl_isolates_report_total"], total)
        self.assertEqual(next(f["queries"] for f in page.context["forms"] if f["key"] == access.CTRL_ISOLATES), total)
        self.assertEqual(page.context["grand_total"], page.context["context_total_issues"])
        take_snapshot()
        rows = QueryCount.objects.filter(form="ctrl_isolates", site__isnull=True)
        self.assertEqual(sum(rows.values_list("count", flat=True)), total)

    def test_ctrl_saves_only_its_own_fields(self):
        ZonalLaboratory.objects.filter(pk=self.b_lab.pk).update(sample_volume=5)
        yes = YesNo.objects.get(value=1)
        self.client.force_login(self.ctrl_tech)
        self.assertContains(self.client.get(self.form_url()), "id_isolate_unique_lab_no")
        response = self.client.post(self.form_url(), {"isolate_unique_lab_no": "ISO-1", "phenotypic_performed": yes.pk})  # ignored
        self.assertRedirects(response, reverse(PAGE), fetch_redirect_response=False)
        lab = ZonalLaboratory.objects.get(pk=self.b_lab.pk)
        self.assertEqual(lab.isolate_unique_lab_no, "ISO-1")
        self.assertEqual(lab.sample_volume, 5)
        self.assertEqual(lab.culture_isolate, self.isolate_yes)
        self.assertIsNone(lab.phenotypic_performed)  # DST comes from TB-LIS, not this form
        self.assertEqual(lab.updated_by, self.ctrl_tech)
        self.assertEqual(get_ctrl_isolate_counts(self.ctrl_tech)["missing_isolate_unique_lab_no"], 0)

    def test_number_is_required_only_when_the_isolate_went_to_ctrl(self):
        self.client.force_login(self.ctrl_tech)
        page = self.client.post(self.form_url(), {"isolate_unique_lab_no": ""})
        self.assertEqual(page.status_code, 200)
        self.assertIn("isolate_unique_lab_no", page.context["form"].errors)
        ZonalLaboratory.objects.filter(pk=self.b_lab.pk).update(culture_isolate=self.isolate_no, isolate_unique_lab_no="WRONG")
        self.client.post(self.form_url(), {"isolate_unique_lab_no": ""})
        self.assertIsNone(ZonalLaboratory.objects.get(pk=self.b_lab.pk).isolate_unique_lab_no)

    def test_ctrl_cannot_open_dar_records_on_this_form(self):
        self.client.force_login(self.ctrl_tech)
        self.assertEqual(self.client.get(self.form_url(self.dar_lab)).status_code, 404)

    def test_viewers_read_the_page_but_cannot_enter(self):
        reviewer = self.make_user("rev_ctrl", [access.REVIEWER])
        self.client.force_login(reviewer)
        page = self.client.get(reverse(PAGE))
        self.assertContains(page, self.pid("B1"))
        self.assertNotContains(page, self.form_url())
        self.assertEqual(self.client.get(self.form_url()).status_code, 403)

    def test_tabs_separate_open_and_complete(self):
        self.client.force_login(self.ctrl_tech)
        self.assertEqual({r["z"].pk for r in self.client.get(reverse(PAGE)).context["rows"]}, {self.b_lab.pk})
        filled = {name: None for name in CTRL_FIELDS}
        filled.update(isolate_unique_lab_no="ISO-2", phenotypic_performed=YesNo.objects.exclude(value=1).first()
                      or YesNo.objects.create(name="No", value=2))
        ZonalLaboratory.objects.filter(pk=self.b_lab.pk).update(**filled)
        self.assertEqual(self.client.get(reverse(PAGE)).context["rows"], [])
        self.assertEqual({r["z"].pk for r in self.client.get(reverse(PAGE), {"tab": "complete"}).context["rows"]}, {self.b_lab.pk})

    def test_zonal_form_shows_ctrl_answers_but_keeps_them(self):
        ZonalLaboratory.objects.filter(pk=self.b_lab.pk).update(isolate_unique_lab_no="ISO-3")
        lab = ZonalLaboratory.objects.get(pk=self.b_lab.pk)
        form = ZonalLaboratoryForm(instance=lab, screening_instance=lab.screening)
        for name in CTRL_FIELDS:
            self.assertNotIn(name, form.fields)
        self.assertIn("ISO-3", [value for _, value in form.ctrl_values])
        self.client.force_login(self.zone_b_tech)
        self.assertContains(self.client.get(reverse("nanopore:zonal-laboratory-update", args=[lab.pk])), "From CTRL:")

    def test_number_without_submission_is_flagged(self):
        ZonalLaboratory.objects.filter(pk=self.b_lab.pk).update(culture_isolate=self.isolate_no, isolate_unique_lab_no="ISO-4")
        admin = self.make_user("admin_flag", [access.ADMIN])
        _, stats, _, lists = get_zonal_dq(admin, ZonalLaboratory)
        self.assertEqual(stats["isolate_no_not_submitted"], 1)
        self.assertEqual(lists["isolate_no_not_submitted"][0]["isolate_unique_lab_no"], "ISO-4")
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse("reports:zonal_quality_report")), "Isolate Number but Not Submitted to CTRL")

    def test_saving_a_number_fills_dst_already_uploaded(self):
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        batch = TblisUploadBatch.objects.create(source_file_name="t.csv")
        TblisRawData.objects.create(labno="51000", upload_batch=batch, raw_data={
            "labno": "51000", "spectype": "Isolate", "ljdst1_date": "2025-06-01"})
        self.client.force_login(self.ctrl_tech)
        self.assertEqual(self.client.get(reverse(PAGE), {"tab": "not-in-tblis"}).context["rows"], [])
        self.client.post(self.form_url(), {"isolate_unique_lab_no": "51000"})
        lab = ZonalLaboratory.objects.get(pk=self.b_lab.pk)
        self.assertEqual(lab.first_line_dst_performed_id, 1)
        self.assertEqual(self.client.get(reverse(PAGE), {"tab": "not-in-tblis"}).context["rows"], [])

    def test_number_missing_from_tblis_is_listed(self):
        ZonalLaboratory.objects.filter(pk=self.b_lab.pk).update(isolate_unique_lab_no="TYPO")
        self.client.force_login(self.ctrl_tech)
        rows = self.client.get(reverse(PAGE), {"tab": "not-in-tblis"}).context["rows"]
        self.assertEqual([r["z"].pk for r in rows], [self.b_lab.pk])
