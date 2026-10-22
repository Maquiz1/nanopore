"""Recycle bin: recoverable deletes that follow how the forms relate (nanopore/recycle_bin.py)."""
from django.urls import reverse

from nanopore.models import ClinicLaboratory, DeletedRecord, EdcsTblisZonal, Diagnosis, RegimenChanges, Screening, ZonalLaboratory
from nanopore.recycle_bin import RestoreError, collect, restore, soft_delete, summarize
from nanopore.test_access import AccessTestBase
from options.models import SampleNumber, YesNo
from utils import access


class RecycleBinTestBase(AccessTestBase):
    # Django clears an instance's pk when it is deleted, so tests keep the ids.
    def setUp(self):
        self.admin = self.make_user("admin", [access.ADMIN])
        self.screening = self.screenings["A1"]
        self.zonal = self.zonal_labs["A1"]
        yes = YesNo.objects.get(name="Yes")
        self.clinic = ClinicLaboratory.objects.create(
            screening=self.screening, sample_received=yes, afb_microscopy_conducted=yes, xpert_mtb_rif_conducted=yes,
            number_received=SampleNumber.objects.create(name="Two", value=2),
        )
        self.diagnosis = Diagnosis.objects.create(screening=self.screening, tb_diagnosis=yes)
        self.edcs = EdcsTblisZonal.objects.create(
            screening=self.screening, unique_lab_no="LAB-A1", culture_performed=yes,
        )
        self.regimens = [
            RegimenChanges.objects.create(screening=self.screening, pid=self.screening.pid, drug=f"drug {i}")
            for i in range(2)
        ]
        self.screening_id, self.zonal_id, self.diagnosis_id = self.screening.pk, self.zonal.pk, self.diagnosis.pk
        self.clinic_id, self.edcs_id = self.clinic.pk, self.edcs.pk
        self.pid = self.screening.pid


class CascadeRulesTests(RecycleBinTestBase):
    def test_screening_takes_all_its_forms(self):
        self.assertEqual(
            summarize(collect(self.screening)),
            {"Screening": 1, "ClinicLaboratory": 1, "ZonalLaboratory": 1, "EdcsTblisZonal": 1,
             "Diagnosis": 1, "RegimenChanges": 2},
        )

    def test_diagnosis_takes_its_regimen_changes(self):
        self.assertEqual(summarize(collect(self.diagnosis)), {"Diagnosis": 1, "RegimenChanges": 2})

    def test_clinic_lab_takes_zonal_lab_and_edcs_tblis(self):
        self.assertEqual(
            summarize(collect(self.clinic)), {"ClinicLaboratory": 1, "ZonalLaboratory": 1, "EdcsTblisZonal": 1}
        )

    def test_zonal_lab_takes_its_edcs_tblis(self):
        self.assertEqual(summarize(collect(self.zonal)), {"ZonalLaboratory": 1, "EdcsTblisZonal": 1})

    def test_uploaded_tblis_rows_are_never_touched(self):
        from nanopore.models import TblisRawData
        raw = TblisRawData.objects.create(labno="LAB-A1", raw_data={"labno": "LAB-A1"})
        soft_delete(self.clinic, self.admin)
        self.assertTrue(TblisRawData.objects.filter(pk=raw.pk).exists())

    def test_other_forms_delete_only_themselves(self):
        self.assertEqual(summarize(collect(self.regimens[0])), {"RegimenChanges": 1})

    def test_restore_order_puts_parent_first(self):
        self.assertIsInstance(collect(self.screening)[0], Screening)


class SoftDeleteRestoreTests(RecycleBinTestBase):
    def test_delete_screening_then_restore_everything(self):
        entry = soft_delete(self.screening, self.admin, reason="duplicate")
        self.assertFalse(Screening.objects.filter(pk=self.screening_id).exists())
        self.assertFalse(RegimenChanges.objects.filter(screening_id=self.screening_id).exists())
        self.assertEqual(entry.total_records, 7)

        restore(entry, self.admin)
        restored = Screening.objects.get(pk=self.screening_id)
        self.assertEqual(restored.pid, self.pid)
        self.assertEqual(ZonalLaboratory.objects.get(pk=self.zonal_id).unique_lab_no, "LAB-A1")
        self.assertEqual(RegimenChanges.objects.filter(screening=restored).count(), 2)
        entry.refresh_from_db()
        self.assertTrue(entry.is_restored)

    def test_delete_diagnosis_keeps_screening(self):
        entry = soft_delete(self.diagnosis, self.admin)
        self.assertTrue(Screening.objects.filter(pk=self.screening_id).exists())
        self.assertFalse(RegimenChanges.objects.filter(screening_id=self.screening_id).exists())
        restore(entry, self.admin)
        self.assertTrue(Diagnosis.objects.filter(pk=self.diagnosis_id).exists())
        self.assertEqual(RegimenChanges.objects.filter(screening_id=self.screening_id).count(), 2)

    def test_delete_clinic_lab_removes_and_restores_zonal_lab(self):
        entry = soft_delete(self.clinic, self.admin)
        self.assertFalse(ZonalLaboratory.objects.filter(pk=self.zonal_id).exists())
        self.assertTrue(Screening.objects.filter(pk=self.screening_id).exists())
        self.assertFalse(EdcsTblisZonal.objects.filter(pk=self.edcs_id).exists())
        restore(entry, self.admin)
        self.assertTrue(ClinicLaboratory.objects.filter(pk=self.clinic_id).exists())
        self.assertTrue(ZonalLaboratory.objects.filter(pk=self.zonal_id).exists())
        self.assertTrue(EdcsTblisZonal.objects.filter(pk=self.edcs_id).exists())

    def test_zonal_lab_waits_for_its_clinic_lab(self):
        zonal_entry = soft_delete(self.zonal, self.admin)
        clinic_entry = soft_delete(self.clinic, self.admin)
        with self.assertRaises(RestoreError):
            restore(zonal_entry, self.admin)
        restore(clinic_entry, self.admin)
        restore(zonal_entry, self.admin)
        self.assertTrue(ZonalLaboratory.objects.filter(pk=self.zonal_id).exists())

    def test_regimen_change_waits_for_its_diagnosis(self):
        regimen_entry = soft_delete(self.regimens[0], self.admin)
        soft_delete(self.diagnosis, self.admin)
        with self.assertRaises(RestoreError):
            restore(regimen_entry, self.admin)

    def test_child_cannot_be_restored_while_screening_is_deleted(self):
        zonal_entry = soft_delete(self.zonal, self.admin)
        soft_delete(self.screening, self.admin)
        with self.assertRaises(RestoreError):
            restore(zonal_entry, self.admin)

    def test_restore_refuses_when_a_newer_record_took_its_place(self):
        entry = soft_delete(self.zonal, self.admin)
        ZonalLaboratory.objects.create(
            screening_id=self.screening_id, unique_lab_no="NEW", culture_performed=YesNo.objects.get(name="Yes"),
        )
        with self.assertRaises(RestoreError):
            restore(entry, self.admin)
        self.assertFalse(DeletedRecord.objects.get(pk=entry.pk).is_restored)

    def test_restore_twice_is_refused(self):
        entry = soft_delete(self.regimens[0], self.admin)
        restore(entry, self.admin)
        with self.assertRaises(RestoreError):
            restore(entry, self.admin)


class RecycleBinViewTests(RecycleBinTestBase):
    def test_only_admins_can_delete(self):
        ds = self.make_user("ds", [access.DATA_SPECIALIST], sites=[self.a1])
        self.client.force_login(ds)
        url = reverse("nanopore:screening-delete", args=[self.screening.pk])
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertEqual(self.client.get(reverse("nanopore:recycle-bin")).status_code, 403)

    def test_admin_delete_page_lists_what_goes_and_moves_it_to_bin(self):
        self.client.force_login(self.admin)
        url = reverse("nanopore:screening-delete", args=[self.screening.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["to_delete"]["RegimenChanges"], 2)

        self.client.post(url, {"reason": "duplicate"})
        entry = DeletedRecord.objects.get()
        self.assertEqual(entry.reason, "duplicate")

        self.assertEqual(self.client.get(reverse("nanopore:recycle-bin")).status_code, 200)
        self.assertEqual(self.client.get(reverse("nanopore:recycle-bin-detail", args=[entry.pk])).status_code, 200)
        self.client.post(reverse("nanopore:recycle-bin-restore", args=[entry.pk]))
        self.assertTrue(Screening.objects.filter(pk=self.screening_id).exists())

    def test_editor_removing_regimen_row_goes_to_bin(self):
        nurse = self.make_user("nurse", [access.NURSE], sites=[self.a1])
        self.client.force_login(nurse)
        response = self.client.delete(reverse("nanopore:regimen-delete", args=[self.regimens[0].pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DeletedRecord.objects.get().model_name, "RegimenChanges")

    def test_new_list_pages_render(self):
        self.client.force_login(self.admin)
        for name in ("nanopore:regimen-list", "nanopore:edcs-tblis-laboratory-list"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
