"""Substudy 4 Zonal Lab forms set aside in the Recycle Bin (nanopore/substudy4_set_aside.py)."""
import csv
import io
import os
import tempfile

from django.core.management import call_command
from django.urls import reverse

from nanopore import recycle_bin
from nanopore.edcs_tblis_cards import card_queryset
from nanopore.models import ClinicLaboratory, DeletedRecord, EdcsTblisZonal, TblisNotInEdcs, ZonalLaboratory
from nanopore.models.system_control import SystemControl
from nanopore.substudy4_set_aside import SET_ASIDE_REASON, set_aside_lab_numbers
from nanopore.tasks_tblis_raw import process_raw_tblis_upload
from nanopore.test_data_safety import DataSafetyBase
from options.models import SampleNumber, XpertMTB, YesNo
from utils import access


class Substudy4SetAsideTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        yes = YesNo.objects.get(pk=1)
        not_detected = XpertMTB.objects.create(pk=1, value=1, name="Not detected")
        number = SampleNumber.objects.create(name="One", value=1)
        # The Dar es Salaam participant is Substudy 4 and was given a Zonal Lab form
        ClinicLaboratory.objects.create(screening=self.dar, sample_received=yes, number_received=number,
                                        afb_microscopy_conducted=yes, xpert_mtb_rif_conducted=yes, xpert_mtb=not_detected)
        self.lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001")
        self.admin = self.make_user("admin_s4", [access.ADMIN])

    def run_command(self, *args):
        out = io.StringIO()
        call_command("set_aside_substudy4_zonal", *args, stdout=out)
        return out.getvalue()

    def test_preview_changes_nothing_then_apply_sets_aside_and_restore_brings_back(self):
        preview = self.run_command()
        self.assertIn("Substudy 4 Zonal Lab forms: 1", preview)
        self.assertIn("Preview only", preview)
        self.assertTrue(ZonalLaboratory.objects.filter(pk=self.lab.pk).exists())

        self.run_command("--apply", "--user", self.admin.username)
        self.assertFalse(ZonalLaboratory.objects.filter(screening=self.dar).exists())
        self.assertFalse(EdcsTblisZonal.objects.filter(screening=self.dar).exists())
        entry = DeletedRecord.objects.get(reason=SET_ASIDE_REASON)
        self.assertEqual((entry.deleted_by, entry.summary), (self.admin, {"ZonalLaboratory": 1, "EdcsTblisZonal": 1}))
        self.assertEqual(set_aside_lab_numbers(), {"30001"})
        # Other zones' Substudy 2 forms are untouched
        self.assertEqual(ZonalLaboratory.objects.count(), 3)

        recycle_bin.restore(entry, self.admin)
        self.assertTrue(ZonalLaboratory.objects.filter(screening=self.dar, unique_lab_no="30001").exists())
        self.assertEqual(set_aside_lab_numbers(), set())

    def test_apply_needs_a_user(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            self.run_command("--apply")

    def test_tblis_rows_of_set_aside_forms_are_not_reported_missing(self):
        self.run_command("--apply", "--user", self.admin.username)
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        csv.writer(handle).writerows([["labno", "spectype", "peripheralres_genexpert"],
                                      ["30001", "Sputum", "MTB Detected"], ["39999", "Sputum", "MTB Detected"]])
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        result = process_raw_tblis_upload.apply(args=[handle.name, None, "s4.csv"]).get()
        self.assertEqual(result["set_aside_substudy4_count"], 1)
        self.assertEqual(list(TblisNotInEdcs.objects.values_list("labno", flat=True)), ["39999"])
        self.assertEqual(list(card_queryset("tblis_not_in_edcs").values_list("labno", flat=True)), ["39999"])

    def test_no_new_zonal_lab_for_substudy_4_except_admins(self):
        self.lab.delete()
        SystemControl.objects.update(zonal_lab_by_section=False)
        create = reverse("nanopore:zonal-laboratory-create") + f"?screening={self.dar.pk}"
        section = reverse("nanopore:zonal-lab-section-new", args=["reception"]) + f"?screening={self.dar.pk}"
        self.client.force_login(self.make_user("ctrl_s4", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        self.assertRedirects(self.client.get(create), reverse("nanopore:form-status-list"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(section).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(create).status_code, 200)
        self.assertEqual(self.client.get(section).status_code, 200)

    def test_dashboard_line(self):
        self.run_command("--apply", "--user", self.admin.username)
        self.client.force_login(self.admin)
        context = self.client.get(reverse("dashboard:dashboard")).context
        self.assertEqual((context["substudy4_set_aside_count"], context["substudy4_zonal_count"]), (1, 0))
