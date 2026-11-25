"""CTRL work (Dar) counted once, under Form queries; the TB-LIS follow-up badge."""
from django.core.cache import cache
from django.test import RequestFactory
from django.urls import reverse

from nanopore.models import EdcsTblisZonal, TblisRawData, TblisUploadBatch, ZonalLaboratory
from nanopore.models.discrepancies import TblisFollowUp
from nanopore.test_data_safety import DataSafetyBase
from reports.context_processors.specific_queries_total import specific_queries_total
from reports.context_processors.tblis_follow_up_context import follow_up_participants
from reports.services.zonal_dq import get_zonal_counts
from reports.services.zonal_dq.ctrl import get_ctrl_dar_counts
from reports.services.zonal_dq.filters import get_zonal_dq_filters
from utils import access


class CtrlDarWorkCountsTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        # A Dar record with nothing yet: Nanopore and LPA questions are CTRL's, the rest TB-LIS's
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001", culture_performed=self.yes)
        self.admin = self.make_user("admin_counts", [access.ADMIN])

    def test_nanopore_and_lpa_bands_are_counted_once_under_ctrl_work(self):
        edcs_keys = set(get_zonal_dq_filters(EdcsTblisZonal))
        self.assertFalse({"missing_nanopore_done", "missing_first_line_drugs", "missing_second_line_drugs"} & edcs_keys)
        self.assertIn("missing_microscopy_type", edcs_keys)  # TB-LIS's stays on EDCS/TBLIS
        dar = get_ctrl_dar_counts(self.admin)
        self.assertEqual(dar["missing_nanopore_done"], 1)
        request = RequestFactory().get("/")
        request.user = self.admin
        total = specific_queries_total(request)["context_specific_queries_total"]
        zonal_total = get_zonal_counts(self.admin, ZonalLaboratory)[1]
        edcs_total = get_zonal_counts(self.admin, EdcsTblisZonal)[1]
        from reports.services.zonal_dq import get_ctrl_isolate_counts
        isolates = sum(get_ctrl_isolate_counts(self.admin).values())
        self.assertGreaterEqual(total, zonal_total + edcs_total + isolates + sum(dar.values()))

    def test_sidebar_and_page(self):
        self.client.force_login(self.make_user("ctrl_counts", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        page = self.client.get(reverse("reports:ctrl_dar_work"))
        self.assertEqual(page.context["query_total"], sum(get_ctrl_dar_counts(self.admin).values()))
        self.assertContains(page, "CTRL work (Dar)")
        self.client.force_login(self.make_user("lab_a_counts", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        self.assertNotContains(self.client.get(reverse("nanopore:zonal-laboratory-list")), "CTRL work (Dar)")


class TblisFollowUpBadgeTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.batch = TblisUploadBatch.objects.create()
        self.lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")

    def test_a_participant_counts_once(self):
        admin = self.make_user("admin_fu", [access.ADMIN])
        self.assertEqual(follow_up_participants(admin), set())
        # Rejected by the latest file (GeneXpert not provided) and also on the not-recorded list
        TblisRawData.objects.create(labno="30001", upload_batch=self.batch,
                                    raw_data={"labno": "30001", "spectype": "Sputum", "peripheralres_genexpert": "Not Provided"})
        TblisFollowUp.objects.create(labno="30001", reason="genexpert_missing", upload_batch=self.batch)
        self.assertEqual(follow_up_participants(admin), {self.dar.pk})
        self.client.force_login(admin)
        page = self.client.get(reverse("nanopore:tblis-follow-up"))
        self.assertEqual(page.context["context_tblis_follow_up_total"], 1)

    def test_only_people_with_the_page_see_it(self):
        self.client.force_login(self.make_user("nurse_fu", [access.NURSE], sites=[self.a1]))
        response = self.client.get(reverse("nanopore:screening-list"))
        self.assertEqual(response.context["context_tblis_follow_up_total"], 0)
