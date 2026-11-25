"""Your work today: each role sees its own tiles (dashboard/work.py)."""
from django.core.cache import cache
from django.urls import reverse

from nanopore.test_data_safety import DataSafetyBase
from utils import access


class WorkPanelTests(DataSafetyBase):
    def tiles(self, user):
        cache.clear()
        self.client.force_login(user)
        groups = self.client.get(reverse("dashboard:dashboard")).context["work_groups"]
        return {tile.label for _, tiles in groups for tile in tiles}

    def test_each_role_sees_its_own_work(self):
        nurse = self.tiles(self.make_user("nurse_w", [access.NURSE], sites=[self.a1]))
        self.assertIn("New screening", nurse)
        self.assertIn("Enrollment forms missing", nurse)
        self.assertNotIn("Zonal Lab queries", nurse)
        self.assertNotIn("Download data", nurse)

        lab = self.tiles(self.make_user("lab_w", [access.LABORATORY_TECHNICIAN], sites=[self.alab]))
        self.assertIn("Zonal Lab queries", lab)
        self.assertNotIn("New screening", lab)
        self.assertNotIn("CTRL work (Dar): Nanopore and LPA", lab)
        self.assertNotIn("EDCS / TB-LIS queries", lab)  # Dar es Salaam's queries

        ctrl = self.tiles(self.make_user("ctrl_w", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        self.assertTrue({"CTRL isolates: numbers to enter", "CTRL work (Dar): Nanopore and LPA",
                         "TB-LIS follow-up", "Last TB-LIS upload"} <= ctrl)

        stat = self.tiles(self.make_user("stat_w", [access.STATISTICIAN], zones=[self.zone_a]))
        self.assertTrue({"Download data", "Data dictionary"} <= stat)
        self.assertNotIn("New screening", stat)
        cache.clear()
        titles = [title for title, _ in self.client.get(reverse("dashboard:dashboard")).context["work_groups"]]
        self.assertIn("Open queries", titles)  # read only: they follow the queries

    def test_counts_match_the_sidebar_and_zero_shows_done(self):
        user = self.make_user("ds_w", [access.DATA_SPECIALIST], zones=[self.zone_a])
        cache.clear()
        self.client.force_login(user)
        page = self.client.get(reverse("dashboard:dashboard"))
        tiles = {t.label: t for _, ts in page.context["work_groups"] for t in ts}
        self.assertEqual(tiles["Zonal Lab queries"].count, page.context["context_zonal_report_total"])
        done = [t for t in tiles.values() if t.count == 0]
        self.assertTrue(all(t.tone == "done" for t in done if t.tone != "info"))
        self.assertContains(page, "Your work today")


class SinceLastVisitTests(DataSafetyBase):
    """Ages from the records' own dates, and the change since the last visit from the daily query snapshot."""

    def test_last_visit_is_kept_for_the_whole_day(self):
        import datetime
        from dashboard.work import remember_visit
        from django.utils import timezone
        user = self.make_user("ds_visit", [access.DATA_SPECIALIST], zones=[self.zone_a])
        self.assertIsNone(remember_visit(user))  # first visit
        profile = user.profile
        profile.dashboard_seen_on = timezone.localdate() - datetime.timedelta(days=3)
        profile.save()
        self.assertEqual(remember_visit(user), timezone.localdate() - datetime.timedelta(days=3))
        self.assertEqual(remember_visit(user), timezone.localdate() - datetime.timedelta(days=3))  # same day: unchanged

    def test_change_since_the_last_visit_and_waiting(self):
        import datetime
        from django.utils import timezone
        from reports.models import QueryCount, QuerySnapshotRun
        user = self.make_user("ds_change", [access.DATA_SPECIALIST], zones=[self.zone_a])
        cache.clear()
        self.client.force_login(user)
        live = {t.label: t for _, ts in self.client.get(reverse("dashboard:dashboard")).context["work_groups"] for t in ts}
        zonal_now = live["Zonal Lab queries"].count
        # Three days ago there were 5 more Zonal Lab queries at site A1
        day = timezone.localdate() - datetime.timedelta(days=3)
        run = QuerySnapshotRun.objects.create(snapshot_date=day)
        QueryCount.objects.create(run=run, zone=self.zone_a, site=self.a1, form=access.ZONAL_LAB, query="missing_x", count=zonal_now + 5)
        profile = user.profile
        profile.dashboard_seen_on = day
        profile.save()
        cache.clear()
        page = self.client.get(reverse("dashboard:dashboard"))
        tiles = {t.label: t for _, ts in page.context["work_groups"] for t in ts}
        self.assertEqual(tiles["Zonal Lab queries"].change, -5)
        self.assertEqual(page.context["work_since"]["date"], day)
        # The base participants were screened on 1 Mar 2025: their missing forms have waited over 30 days
        self.assertEqual(tiles["Enrollment forms missing"].waiting, tiles["Enrollment forms missing"].count)


class SitesAtAGlanceTests(DataSafetyBase):
    def test_who_sees_it(self):
        cache.clear()
        self.client.force_login(self.make_user("coord_sites", [access.COORDINATOR], zones=[self.zone_a]))
        page = self.client.get(reverse("dashboard:dashboard"))
        self.assertIn("site_rows", page.context)
        self.assertEqual({r.name for r in page.context["site_rows"]}, {"A1", "A2"})  # their zone's sites with participants
        cache.clear()
        self.client.force_login(self.make_user("nurse_sites", [access.NURSE], sites=[self.a1]))
        self.assertNotIn("site_rows", self.client.get(reverse("dashboard:dashboard")).context)

    def test_flags_a_site_well_behind(self):
        from dashboard.sites import SiteRow
        from locations.models import Site
        Site.objects.filter(pk__in=[self.a1.pk, self.a2.pk]).update(substudy2Target=10)
        admin = self.make_user("admin_sites", [access.ADMIN])
        from dashboard.sites import sites_at_a_glance
        rows, _ = sites_at_a_glance(admin)
        self.assertTrue(all(isinstance(r, SiteRow) for r in rows))
        self.assertEqual({r.name: r.target for r in rows if r.name in ("A1", "A2")}, {"A1": 10, "A2": 10})
