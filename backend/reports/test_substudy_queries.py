import datetime

from django.core.cache import cache
from django.urls import reverse

from nanopore.test_access import AccessTestBase
from nanopore.test_dashboard import SubstudyConsistencyTests
from reports.models import QueryCount, QuerySnapshotRun
from reports.services.query_snapshot import take_snapshot
from reports.services.substudy_queries import substudy_query_counts
from utils import access


class SubstudyQueriesTests(SubstudyConsistencyTests):
    """Participants from SubstudyConsistencyTests: 001 Substudy 2 (with the base Zonal Lab),
    002 / 003 Substudy 4, 004 / 005 Uncategorized, all enrolled."""

    def setUp(self):
        super().setUp()
        cache.clear()  # sidebar counts are cached per user id
        from nanopore.models import Diagnosis, Screening, ZonalLaboratory
        from options.models import TBTreatmentOutcome, YesNo
        yes = YesNo.objects.get(name="Yes")
        cured = TBTreatmentOutcome.objects.create(pk=1, value=1, name="Cured")
        Screening.objects.update(eligible=True)  # save() works eligibility out from answers the fixture skips
        screening = {pid: Screening.objects.get(pk=pk) for pid, pk in self.screening_ids.items()}
        Diagnosis.objects.create(screening=screening["002"], tb_diagnosis=yes, tb_outcome2=cured)
        Diagnosis.objects.create(screening=screening["005"], tb_diagnosis=yes, tb_outcome2=cured)
        self.ss4_zonal = ZonalLaboratory.objects.create(screening=screening["003"], unique_lab_no="LAB-003", culture_performed=yes)

    def test_sidebar_has_its_own_link(self):
        page = self.client.get(reverse("dashboard:dashboard"))
        self.assertContains(page, reverse("reports:substudy_queries"))
        self.assertEqual(page.context["context_substudy_queries_total"], 4)

    def test_each_query_finds_its_participants(self):
        admin = self.make_user("boss", [access.ADMIN])
        counts = substudy_query_counts(admin, site_id=self.a1.id)
        self.assertEqual(counts, {
            "ss2_no_zonal": 0,
            "ss4_with_zonal": 1,               # 003
            "ss2_no_outcome": 1,               # 001: enrolled, no Diagnosis yet
            "ss4_with_outcome": 1,             # 002
            "uncategorized_with_outcome": 1,   # 005
        })

    def test_page_offers_the_fixes(self):
        page = self.client.get(reverse("reports:substudy_queries", args=["ss4_with_zonal"]))
        self.assertEqual(page.status_code, 200)
        delete_url = reverse("nanopore:zonal-laboratory-delete", args=[self.ss4_zonal.pk])
        self.assertContains(page, delete_url + "?next=")
        self.assertContains(page, "LAB-003")

    def test_lab_technician_sees_only_lab_queries(self):
        tech = self.make_user("tech", [access.LABORATORY_TECHNICIAN], zones=[self.zone_a])
        self.assertEqual(set(substudy_query_counts(tech)), {"ss2_no_zonal", "ss4_with_zonal"})
        self.client.force_login(tech)
        page = self.client.get(reverse("reports:substudy_queries", args=["ss4_with_outcome"]))
        self.assertIn(page.context["selected"].key, {"ss2_no_zonal", "ss4_with_zonal"})  # not an outcome query

    def test_completed_is_substudy_2_with_an_outcome(self):
        # 002 (Substudy 4) and 005 (Uncategorized) have outcomes but are not "completed"
        dashboard = self.client.get(reverse("dashboard:dashboard")).context
        self.assertEqual(dashboard["diagnosis_outcome_count"], 0)
        summary = self.client.get(reverse("reports:completed_study_summary")).context
        self.assertEqual(summary["total_completed"], 0)

    def test_snapshot_matches_the_sidebar_and_replaces_the_day(self):
        sidebar_total = self.client.get(reverse("dashboard:dashboard")).context["context_total_issues"]
        take_snapshot()
        run, _ = take_snapshot()  # same day again: replaced, not added
        self.assertEqual(QuerySnapshotRun.objects.count(), 1)
        all_sites = sum(QueryCount.objects.filter(run=run, site__isnull=True).values_list("count", flat=True))
        self.assertEqual(all_sites, sidebar_total)
        self.assertTrue(QueryCount.objects.filter(run=run, site=self.a1, form="missing_forms", query="clinic_lab").exists())
        self.assertFalse(QueryCount.objects.filter(form="substudy").exists())  # a list, not a trend

    def test_trends_page_shows_the_change(self):
        take_snapshot(datetime.date.today() - datetime.timedelta(days=1))
        QueryCount.objects.filter(site__isnull=True, form="missing_forms", query="clinic_lab").update(count=7)
        take_snapshot()
        page = self.client.get(reverse("reports:query_trends"))
        self.assertEqual(page.status_code, 200)
        kpis = page.context["kpis"]
        self.assertEqual(kpis["since_previous"], -4)  # 7 Clinic Lab forms missing yesterday, 3 today
        self.assertEqual(len(page.context["chart"]["labels"]), 2)

        # Per zone / site / form / query type, and a date range
        rows = lambda **params: {r["label"]: r["days"] for r in self.client.get(reverse("reports:query_trends"), params).context["table"]}
        self.assertIn("Zone A", rows(group="zone"))
        self.assertIn("A1 (Zone A)", rows(group="site"))
        self.assertEqual(rows(group="form", type="missing")["Clinic Lab"], [3, 7])  # forms not filled, latest first
        self.assertEqual(set(rows(group="type")), {"Missing forms", "Form queries"})
        today = datetime.date.today().isoformat()
        self.assertEqual(len(self.client.get(reverse("reports:query_trends"), {"start": today, "end": today}).context["days"]), 1)
        self.assertEqual(self.client.get("/reports/dq/missing-forms/").status_code, 302)


class QueryTrendsAccessTests(AccessTestBase):
    def test_who_sees_query_trends(self):
        url = reverse("reports:query_trends")
        allowed = [
            self.make_user("ds", [access.DATA_SPECIALIST], zones=[self.zone_a]),
            self.make_user("dm", [access.DATA_MANAGER], zones=[self.zone_a]),
            self.make_user("coord", [access.COORDINATOR], zones=[self.zone_a]),
            self.make_user("coord2", zones=[self.zone_a], position="Coordinator"),  # by position
            self.make_user("stat", [access.STATISTICIAN], sites=[self.a1]),
            self.make_user("rev", [access.REVIEWER]),
            self.make_user("rev2", position="Reviewer"),  # by position
        ]
        for user in allowed:
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 200, user.username)
        self.client.force_login(self.make_user("nurse", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_statistician_and_reviewer_see_the_data_quality_section(self):
        trends = reverse("reports:query_trends")
        download = reverse("reports:substudy_download", args=["substudy2"])
        users = [self.make_user("stat", [access.STATISTICIAN], sites=[self.a1]), self.make_user("rev", [access.REVIEWER])]
        for user in users:
            cache.clear()
            self.client.force_login(user)
            page = self.client.get(reverse("dashboard:dashboard"))
            self.assertContains(page, "Data quality")
            self.assertContains(page, trends)
            self.assertContains(page, download)
            self.assertContains(page, reverse("reports:substudy_queries"))
            self.assertContains(page, reverse("reports:date_issues"))
            self.assertEqual(self.client.get(download).status_code, 200, user.username)

    def test_substudy_download_link_stays_hidden_from_others(self):
        cache.clear()
        self.client.force_login(self.make_user("nurse", [access.NURSE], sites=[self.a1]))
        self.assertNotContains(self.client.get(reverse("dashboard:dashboard")),
                               reverse("reports:substudy_download", args=["substudy2"]))

    def test_reviewer_trends_count_not_eligible_like_the_live_page(self):
        from reports.services.query_snapshot import is_visible
        self.assertTrue(is_visible(self.make_user("rev", [access.REVIEWER]), "screening", "not_eligible"))
        self.assertFalse(is_visible(self.make_user("stat", [access.STATISTICIAN], sites=[self.a1]), "screening", "not_eligible"))
