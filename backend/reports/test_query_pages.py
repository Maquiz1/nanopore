"""EDCS/TBLIS query page: each list shows its first records; a query's full list has its own pages."""
from datetime import date

from django.core.cache import cache
from django.urls import reverse

from locations.models import District, Region, Site, Zone
from nanopore.models import EdcsTblisZonal, Screening, ZonalLaboratory
from nanopore.test_access import AccessTestBase
from utils import access

URL = "reports:edcs_tblis_quality_report"


class EdcsQueryPagesTests(AccessTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        country = cls.zone_a.country
        dar = Zone.objects.create(name="Dar es salaam", country=country)
        district = District.objects.create(name="Temeke", region=Region.objects.create(name="Dar region", country=country, zone=dar))
        cls.temeke = Site.objects.create(name="Temeke Hospital", district=district, pid_prefix="DF_TZ_SS2_18_", site_level=cls.a1.site_level)
        cls.ilala = Site.objects.create(name="Ilala", district=district, pid_prefix="DF_TZ_SS2_16_", site_level=cls.a1.site_level)
        for i in range(60):
            site = cls.temeke if i < 55 else cls.ilala
            screening = Screening.objects.create(screening_date=date(2025, 3, 1), pid1=f"{i:03}", pid2=f"{i:03}", site=site, eligible=True)
            ZonalLaboratory.objects.create(screening=screening, unique_lab_no=f"3{i:04}")
            EdcsTblisZonal.objects.create(screening=screening, unique_lab_no=f"3{i:04}")  # no date received: a query for all 60

    def setUp(self):
        cache.clear()
        self.client.force_login(self.make_user("admin_pages", [access.ADMIN]))

    def test_each_list_shows_its_first_records_and_a_link_to_all(self):
        page = self.client.get(reverse(URL))
        self.assertEqual(len(page.context["missing_date_sputum_received"]), 25)
        self.assertEqual(page.context["count_missing_date_sputum_received"], 60)
        self.assertContains(page, "Showing 25 of 60")
        self.assertContains(page, "?query=missing_date_sputum_received")

    def test_a_query_has_its_own_pages(self):
        first = self.client.get(reverse(URL), {"query": "missing_date_sputum_received"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual((len(first.context["rows"]), first.context["page_obj"].paginator.count), (50, 60))
        second = self.client.get(reverse(URL), {"query": "missing_date_sputum_received", "page": 2})
        self.assertEqual(len(second.context["rows"]), 10)
        pids = {row["pid"] for row in first.context["rows"]} | {row["pid"] for row in second.context["rows"]}
        self.assertEqual(len(pids), 60)
        self.assertContains(first, reverse("nanopore:zonal-laboratory-update", args=[ZonalLaboratory.objects.first().pk]))

    def test_filters_carry_into_the_full_list(self):
        page = self.client.get(reverse(URL), {"query": "missing_date_sputum_received", "site": self.ilala.pk})
        self.assertEqual(page.context["page_obj"].paginator.count, 5)
        self.assertContains(page, f"site={self.ilala.pk}")

    def test_unknown_query_is_not_found(self):
        self.assertEqual(self.client.get(reverse(URL), {"query": "no_such_query"}).status_code, 404)

    def test_full_list_follows_the_users_sites(self):
        self.client.force_login(self.make_user("ds_pages", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        page = self.client.get(reverse(URL), {"query": "missing_date_sputum_received"})
        self.assertEqual(page.context["page_obj"].paginator.count, 0)


class ZonalQueryPagesTests(AccessTestBase):
    URL = "reports:zonal_quality_report"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(55):
            screening = Screening.objects.create(screening_date=date(2025, 3, 1), pid1=f"5{i:02}", pid2=f"5{i:02}",
                                                 site=cls.b1, eligible=True)
            ZonalLaboratory.objects.create(screening=screening, unique_lab_no=f"Z{i:04}")  # no date received

    def setUp(self):
        cache.clear()
        self.client.force_login(self.make_user("admin_zpages", [access.ADMIN]))

    def test_each_list_shows_its_first_records_and_a_link_to_all(self):
        page = self.client.get(reverse(self.URL))
        total = page.context["count_missing_date_sputum_received"]
        self.assertGreater(total, 25)
        self.assertEqual(len(page.context["missing_date_sputum_received"]), 25)
        self.assertContains(page, f"Showing 25 of {total}")
        self.assertContains(page, "?query=missing_date_sputum_received")

    def test_a_query_has_its_own_pages_with_zonal_lab_links(self):
        page = self.client.get(reverse(self.URL), {"query": "missing_date_sputum_received"})
        total = page.context["page_obj"].paginator.count
        self.assertEqual((len(page.context["rows"]), page.context["page_obj"].paginator.num_pages), (50, 2))
        last = self.client.get(reverse(self.URL), {"query": "missing_date_sputum_received", "page": 2})
        self.assertEqual(len(last.context["rows"]), total - 50)
        lab = ZonalLaboratory.objects.get(unique_lab_no="Z0000")
        both = page.content.decode() + last.content.decode()
        self.assertIn(reverse("nanopore:zonal-laboratory-update", args=[lab.pk]), both)
        self.assertContains(page, "Isolate Lab No.")
        self.assertContains(page, reverse(self.URL))

    def test_filters_and_unknown_queries(self):
        page = self.client.get(reverse(self.URL), {"query": "missing_date_sputum_received", "zone": self.zone_a.pk})
        self.assertNotIn("Z0000", page.content.decode())
        self.assertEqual(self.client.get(reverse(self.URL), {"query": "missing_isolate_unique_lab_no"}).status_code, 404)  # a CTRL query
