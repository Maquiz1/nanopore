from django.urls import reverse

from nanopore.edcs_tblis_cards import CARDS
from nanopore.models import EdcsTblisZonal, TblisRawData, TblisUploadBatch
from nanopore.tasks_csv_export import _build_edcs_qs, _build_tblis_qs
from nanopore.test_access import AccessTestBase
from utils import access


class EdcsTblisCardsTests(AccessTestBase):
    """Each card's number equals the list it opens and its Excel export."""

    def setUp(self):
        from locations.models import Site
        # A Dar es Salaam (CTRL) participant merged from TB-LIS, plus one not in TB-LIS
        ctrl_site = Site.objects.create(name="CTRL", district=self.a1.district, pid_prefix="DF_TZ_SS2_16_", site_level=self.a1.site_level)
        from nanopore.models import Screening, ZonalLaboratory
        from options.models import YesNo
        yes = YesNo.objects.get(name="Yes")
        batch = TblisUploadBatch.objects.create(source_file_name="tblis.xlsx")
        for n, merged in (("001", True), ("002", None)):
            screening = Screening.objects.create(screening_date="2025-03-01", pid1=n, pid2=n, site=ctrl_site, eligible=True)
            ZonalLaboratory.objects.create(screening=screening, unique_lab_no=f"DSM-{n}", culture_performed=yes)
            EdcsTblisZonal.objects.create(screening=screening, unique_lab_no=f"DSM-{n}")
            if merged:
                TblisRawData.objects.create(upload_batch=batch, labno=f"DSM-{n}", is_merged=True, raw_data={})
        TblisRawData.objects.create(upload_batch=batch, labno="ONLY-IN-TBLIS", is_merged=False, raw_data={})
        self.client.force_login(self.make_user("admin", [access.ADMIN]))

    def test_card_list_and_export_agree(self):
        url = reverse("nanopore:edcs-tblis-laboratory-list")
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        counts = {item["card"].key: item["count"] for section in page.context["sections"] for item in section["cards"]}
        self.assertEqual(set(counts), set(CARDS))
        for key, count in counts.items():
            listed = self.client.get(url, {"card_type": key}).context["paginator"].count
            build = _build_tblis_qs if CARDS[key].source == "tblis" else _build_edcs_qs
            self.assertEqual((count, listed, build({"card_type": key}).count()), (count, count, count), key)
        self.assertEqual((counts["merged"], counts["edcs_not_in_tblis"], counts["tblis_not_in_edcs"]), (1, 1, 1))

    def test_pages_keep_the_card_and_filters(self):
        page = self.client.get(reverse("nanopore:edcs-tblis-laboratory-list"), {"card_type": "ctrl", "zone": self.zone_a.id})
        self.assertIn("card_type=ctrl", page.context["query_params"])
        self.assertIn(f"zone={self.zone_a.id}", page.context["query_params"])

    def test_site_users_do_not_see_raw_tblis_rows(self):
        tech = self.make_user("tech", [access.LABORATORY_TECHNICIAN], zones=[self.zone_a])
        self.client.force_login(tech)
        page = self.client.get(reverse("nanopore:edcs-tblis-laboratory-list"))
        keys = {item["card"].key for section in page.context["sections"] for item in section["cards"]}
        self.assertNotIn("total_tblis", keys)
        self.assertEqual(self.client.get(reverse("nanopore:edcs-tblis-laboratory-list"), {"card_type": "total_tblis"}).context["paginator"].count, 0)
