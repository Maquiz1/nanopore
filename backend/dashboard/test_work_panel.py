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
