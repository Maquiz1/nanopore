"""CTRL's own Dar es Salaam forms (Nanopore and LPA checkboxes), and Dar's isolate and DST queries."""
import re
from datetime import date

from django.core.cache import cache
from django.urls import NoReverseMatch, reverse

from locations.models import District, Region, Site, SiteLevel, Zone
from nanopore.models import EdcsTblisZonal, Screening, ZonalLaboratory
from nanopore.test_access import AccessTestBase
from options.models import FirstLineDrugs, MGITCultureResult, NanoporeSequencingResults, SecondLineDrugs, YesNo, YesNoNA
from utils import access


class CtrlDarFormsTests(AccessTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.yes = YesNo.objects.get(pk=1)
        cls.no = YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})[0]
        cls.iso_yes = YesNoNA.objects.create(pk=1, name="Yes", value=1)
        cls.iso_no = YesNoNA.objects.create(pk=2, name="No", value=2)
        country = cls.zone_a.country
        dar = Zone.objects.create(name="Dar es salaam", country=country)
        region = Region.objects.create(name="Dar region", country=country, zone=dar)
        district = District.objects.create(name="Temeke", region=region)
        cls.ctrl = Site.objects.create(name="CTRL Laboratory", district=district, pid_prefix="CT-",
                                       site_level=SiteLevel.objects.get(code="zonal"))
        site = Site.objects.create(name="Temeke Hospital", district=district, pid_prefix="DF_TZ_SS2_18_",
                                   site_level=SiteLevel.objects.get(code="local"))
        cls.screening = Screening.objects.create(screening_date=date(2025, 3, 1), pid1="002", pid2="002", site=site, eligible=True)
        cls.lab = ZonalLaboratory.objects.create(screening=cls.screening, unique_lab_no="30001")
        cls.edcs = EdcsTblisZonal.objects.create(screening=cls.screening, unique_lab_no="30001")

    def setUp(self):
        cache.clear()
        self.tech = self.make_user("ctrl_t", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl])
        self.client.force_login(self.tech)

    def url(self, name, lab=None):
        return reverse(f"nanopore:ctrl-dar-{name}", args=[(lab or self.lab).pk])

    def rows(self, tab):
        return [r.pk for r in self.client.get(reverse("reports:ctrl_dar_work"), {"tab": tab}).context["page_obj"]]

    def test_no_isolate_form_or_tab_for_dar(self):
        with self.assertRaises(NoReverseMatch):
            self.url("isolate")
        page = self.client.get(reverse("reports:ctrl_dar_work"))
        self.assertEqual([t["key"] for t in page.context["tabs"]], ["nanopore", "lpa"])
        self.assertEqual(page.context["tab"], "nanopore")

    def test_dar_zonal_form_links_to_ctrl_forms_also_once_answered(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(nanopore_done=self.no)
        page = self.client.get(reverse("nanopore:zonal-laboratory-update", args=[self.lab.pk]))
        self.assertContains(page, self.url("nanopore"))
        self.assertContains(page, self.url("lpa"))

    def test_sidebar_badge_counts_both_lists(self):
        badge = lambda: self.client.get(reverse("reports:ctrl_dar_work")).context["context_ctrl_dar_work_total"]
        self.assertEqual(badge(), 1)  # needs Nanopore
        EdcsTblisZonal.objects.filter(pk=self.edcs.pk).update(first_line_lpa=self.yes)
        cache.clear()
        self.assertEqual(badge(), 2)  # and LPA checkboxes
        self.assertContains(self.client.get(reverse("reports:ctrl_dar_work")), '<span class="sb-badge">2</span>', html=True)
        EdcsTblisZonal.objects.filter(pk=self.edcs.pk).update(first_line_lpa=self.no, nanopore_done=self.no)
        cache.clear()
        page = self.client.get(reverse("reports:ctrl_dar_work"))
        self.assertEqual(page.context["context_ctrl_dar_work_total"], 0)

    def test_dar_isolate_answers_are_never_queries(self):
        from reports.services.zonal_dq import get_zonal_counts
        EdcsTblisZonal.objects.filter(pk=self.edcs.pk).update(culture_isolate=self.iso_yes, isolate_unique_lab_no=None)
        stats = get_zonal_counts(self.make_user("admin_iso", [access.ADMIN]), EdcsTblisZonal)[0]
        for key in ("missing_culture_isolate", "missing_isolate_date", "missing_isolate_unique_lab_no", "isolate_no_not_submitted"):
            self.assertNotIn(key, stats)

    def test_positive_culture_stays_a_query_until_dst_is_done(self):
        from reports.services.zonal_dq import get_zonal_counts
        admin = self.make_user("admin_dst", [access.ADMIN])
        record = EdcsTblisZonal.objects.filter(pk=self.edcs.pk)
        count = lambda: get_zonal_counts(admin, EdcsTblisZonal)[0]["missing_phenotypic_performed"]
        self.assertEqual(count(), 0)  # no positive culture
        positive = MGITCultureResult.objects.create(pk=1, name="Positive", value=1)
        negative = MGITCultureResult.objects.create(pk=2, name="Negative", value=2)
        record.update(mgit_results=negative, phenotypic_performed=None)
        self.assertEqual(count(), 0)
        record.update(mgit_results=positive)
        self.assertEqual(count(), 1)  # blank
        record.update(phenotypic_performed=self.no)
        self.assertEqual(count(), 1)  # the upload's No
        record.update(phenotypic_performed=self.yes)
        self.assertEqual(count(), 0)

    def test_edcs_query_page_has_no_isolate_column(self):
        self.client.force_login(self.make_user("admin_col", [access.ADMIN]))
        self.assertNotContains(self.client.get(reverse("reports:edcs_tblis_quality_report")), "Isolate Lab No.")

    def test_nanopore_demands_what_each_answer_opens(self):
        page = self.client.post(self.url("nanopore"), {})
        self.assertIn("nanopore_done", page.context["form"].errors)
        page = self.client.post(self.url("nanopore"), {"nanopore_done": self.yes.pk})
        for name in ("nanopore_sequencing_date", "epi_to_me", "nanopore_results", "sequencing_delayed"):
            self.assertIn(name, page.context["form"].errors)
        response = self.client.post(self.url("nanopore"), {"nanopore_done": self.no.pk, "nanopore_sequencing_date": "2025-05-01"})
        self.assertEqual(response.status_code, 302)
        lab = ZonalLaboratory.objects.get(pk=self.lab.pk)
        self.assertEqual(lab.nanopore_done, self.no)
        self.assertIsNone(lab.nanopore_sequencing_date)  # hidden answers are cleared
        self.assertEqual(EdcsTblisZonal.objects.get(pk=self.edcs.pk).nanopore_done, self.no)
        self.assertEqual(self.rows("nanopore"), [])

    def test_nanopore_yes_saves_when_complete(self):
        result = NanoporeSequencingResults.objects.create(pk=2, name="None", value=2)
        response = self.client.post(self.url("nanopore"), {
            "nanopore_done": self.yes.pk, "nanopore_sequencing_date": "2025-05-01", "epi_to_me": self.no.pk,
            "nanopore_results": result.pk, "sequencing_delayed": self.no.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ZonalLaboratory.objects.get(pk=self.lab.pk).nanopore_results, result)

    def test_lpa_form_shows_only_lines_tblis_says_were_done(self):
        band1 = FirstLineDrugs.objects.create(name="rpoB", value=1)
        band2 = SecondLineDrugs.objects.create(name="gyrA", value=1)
        self.assertContains(self.client.get(self.url("lpa")), "nothing to enter")
        EdcsTblisZonal.objects.filter(pk=self.edcs.pk).update(first_line_lpa=self.yes)
        page = self.client.get(self.url("lpa"))
        self.assertEqual(set(page.context["form"].fields), {"first_line_drugs"})
        self.assertEqual(self.rows("lpa"), [self.edcs.pk])
        page = self.client.post(self.url("lpa"), {})
        self.assertIn("first_line_drugs", page.context["form"].errors)
        self.client.post(self.url("lpa"), {"first_line_drugs": [band1.pk]})
        self.assertEqual(list(ZonalLaboratory.objects.get(pk=self.lab.pk).first_line_drugs.all()), [band1])
        self.assertEqual(list(EdcsTblisZonal.objects.get(pk=self.edcs.pk).first_line_drugs.all()), [band1])
        self.assertEqual(self.rows("lpa"), [])

    def test_forms_leave_tblis_results_alone(self):
        EdcsTblisZonal.objects.filter(pk=self.edcs.pk).update(first_line_lpa=self.yes)
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(first_line_lpa=self.yes, remarks="Kept")
        self.client.post(self.url("nanopore"), {"nanopore_done": self.no.pk})
        lab = ZonalLaboratory.objects.get(pk=self.lab.pk)
        self.assertEqual((lab.remarks, lab.first_line_lpa), ("Kept", self.yes))

    def test_other_zones_do_not_use_these_forms(self):
        self.assertEqual(self.client.get(self.url("nanopore", self.zonal_labs["B1"])).status_code, 404)

    def test_who_can_use_them(self):
        self.assertContains(self.client.get(reverse("dashboard:dashboard")), reverse("reports:ctrl_dar_work"))
        self.client.force_login(self.make_user("rev_d", [access.REVIEWER]))
        self.assertEqual(self.client.get(self.url("nanopore")).status_code, 200)
        self.assertNotContains(self.client.get(self.url("nanopore")), 'type="submit"')
        self.assertEqual(self.client.post(self.url("nanopore"), {"nanopore_done": self.no.pk}).status_code, 403)
        self.client.force_login(self.make_user("lab_d", [access.LABORATORY_TECHNICIAN], zones=[self.zone_a]))
        self.assertEqual(self.client.get(reverse("reports:ctrl_dar_work")).status_code, 403)
        self.assertEqual(self.client.get(self.url("nanopore")).status_code, 403)

    def test_answered_no_is_never_a_query_only_blank_is(self):
        from reports.services.zonal_dq import get_zonal_counts
        admin = self.make_user("admin_no", [access.ADMIN])
        blank = get_zonal_counts(admin, EdcsTblisZonal)[0]
        self.assertEqual(blank["missing_nanopore_done"], 1)
        # Old answers left behind a No don't raise anything
        EdcsTblisZonal.objects.filter(pk=self.edcs.pk).update(nanopore_done=self.no, epi_to_me=self.yes, sequencing_delayed=self.yes,
                                                              nanopore_results=NanoporeSequencingResults.objects.create(pk=1, name="R", value=1))
        stats = get_zonal_counts(admin, EdcsTblisZonal)[0]
        nano = {k: v for k, v in stats.items() if v and any(w in k for w in ("nano", "epi", "sequencing"))}
        self.assertEqual(nano, {})
        # A Yes still asks what it opens
        EdcsTblisZonal.objects.filter(pk=self.edcs.pk).update(nanopore_done=self.yes)
        stats = get_zonal_counts(admin, EdcsTblisZonal)[0]
        self.assertEqual((stats["missing_nanopore_sequencing_date"], stats["missing_epi_to_me_date"]), (1, 1))

    def test_zonal_form_clears_what_a_no_hides(self):
        from nanopore.forms.laboratory.nanopore_rules import settle_nanopore
        from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
        form = ZonalLaboratoryForm(screening_instance=self.screenings["B1"])
        form._errors = {}
        cleaned = {"nanopore_done": self.no, "epi_to_me": self.yes, "epi_to_me_date": date(2025, 1, 1), "sequencing_delayed": self.yes}
        settle_nanopore(form, cleaned)
        self.assertIsNone(cleaned["epi_to_me"])
        self.assertIsNone(cleaned["epi_to_me_date"])
        self.assertFalse(form.errors)

    def test_every_nanopore_question_hides_with_its_label(self):
        page = self.client.get(self.url("nanopore")).content.decode()
        self.assertIn("data-nano-section", page)
        self.assertIn("custom_js/nanopore_section.js", page)
        for rule in ("done", "epi", "results", "delayed", "other-reason"):
            self.assertIn(f'data-nano-when="{rule}"', page)
        self.assertEqual(len(re.findall(r'class="[^"]*\bnano-q\b', page)), 27)  # 11 questions + 16 drugs
