"""Change history of every form (nanopore/history.py): real changes only, where they came from, and why."""
import csv
import os
import tempfile
from datetime import date

from django.urls import reverse

from nanopore import history
from nanopore.models import Diagnosis, EdcsTblisZonal, RegimenChanges, Screening, ZonalLaboratory
from nanopore.tasks_tblis_raw import process_raw_tblis_upload, sync_zonal_laboratory_daily
from nanopore.test_data_safety import DataSafetyBase
from options.models import CultureMethod, MGITCultureResult, YesNoNA
from utils import access


class HistoryTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        self.lab = ZonalLaboratory.objects.get(pk=self.zonal_labs["A1"].pk)
        self.lab.history.all().delete()

    def entries(self, record):
        return list(record.history.order_by("history_date", "history_id"))

    def test_only_real_changes_are_recorded(self):
        self.lab.remarks = "First"
        self.lab.save()
        self.lab.save()  # nothing changed
        self.lab.remarks = "Second"
        self.lab.save()
        self.assertEqual([h.remarks for h in self.entries(self.lab)], ["First", "Second"])

    def test_a_save_and_its_checkboxes_are_one_entry(self):
        lj, mgit = CultureMethod.objects.create(pk=1, name="LJ", value=1), CultureMethod.objects.create(pk=2, name="MGIT", value=2)
        self.lab.culture_method.set([lj])
        self.lab.remarks = "With MGIT"
        self.lab.save()
        self.lab.culture_method.set([mgit])
        last = self.entries(self.lab)[-1]
        self.assertEqual(len(self.entries(self.lab)), 2)
        self.assertEqual((last.remarks, [m.culturemethod_id for m in last.culture_method.all()]), ("With MGIT", [mgit.pk]))

    def test_source_user_and_reason_are_kept(self):
        # A Dar es Salaam form: only the lab number, remarks and the reason
        lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001", remarks="Before")
        user = self.make_user("ds_hist", [access.DATA_SPECIALIST], zones=[self.dar.site.district.region.zone])
        self.client.force_login(user)
        url = reverse("nanopore:zonal-laboratory-update", args=[lab.pk])
        page = self.client.post(url, {"screening": self.dar.pk, "unique_lab_no": "30001", "remarks": "After", "next": "/"})
        self.assertIn("reason_for_change", page.context["form"].errors)  # correcting a saved answer needs a reason
        response = self.client.post(url, {"screening": self.dar.pk, "unique_lab_no": "30001", "remarks": "After",
                                          "reason_for_change": "Typo on the paper form", "next": "/"})
        self.assertEqual(response.status_code, 302)
        last = self.entries(lab)[-1]
        self.assertEqual((last.remarks, last.history_user, last.history_change_reason, last.history_source),
                         ("After", user, "Typo on the paper form", "Form"))

    def test_first_entry_needs_no_reason(self):
        lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        lab.delete()
        self.client.force_login(self.make_user("ctrl_hist", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        response = self.client.post(reverse("nanopore:zonal-laboratory-create") + f"?screening={self.dar.pk}",
                                    {"screening": self.dar.pk, "unique_lab_no": "30002", "next": "/"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ZonalLaboratory.objects.get(screening=self.dar).history.get().history_type, "+")

    def test_tblis_upload_and_nightly_sync_are_named(self):
        lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        MGITCultureResult.objects.create(pk=1, name="Positive", value=1)
        YesNoNA.objects.create(pk=3, name="Na", value=98)
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        csv.writer(handle).writerows([["labno", "spectype", "peripheralres_genexpert", "mgit_res"], ["30001", "Sputum", "MTB Detected", "POSITIVE"]])
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        process_raw_tblis_upload.apply(args=[handle.name, None, "file-23-oct.csv"]).get()
        edcs = EdcsTblisZonal.objects.get(screening=self.dar)
        self.assertEqual(self.entries(edcs)[-1].history_source, "TB-LIS upload: file-23-oct.csv")
        count = edcs.history.count()
        sync_zonal_laboratory_daily.apply().get()
        self.assertEqual(edcs.history.count(), count)  # nothing changed overnight
        ZonalLaboratory.objects.filter(pk=lab.pk).update(remarks="Changed by hand")
        sync_zonal_laboratory_daily.apply().get()
        self.assertEqual(self.entries(edcs)[-1].history_source, "Nightly sync")

    def test_every_form_keeps_history(self):
        screening = self.screenings["A1"]
        screening.screening_date = date(2025, 3, 2)
        screening.save()
        regimen = RegimenChanges.objects.create(screening=screening, date=date(2025, 5, 1), drug="X")
        for record in (screening, regimen):
            self.assertTrue(record.history.exists(), type(record).__name__)
        for model in (Screening, ZonalLaboratory, EdcsTblisZonal, Diagnosis, RegimenChanges):
            self.assertTrue(hasattr(model, "history"), model.__name__)

    def test_history_page_shows_question_labels_and_follows_access(self):
        self.lab.remarks = "Before"
        self.lab.save()
        self.lab.remarks = "After"
        self.lab._change_reason = "Checked against the register"
        self.lab.save()
        url = reverse("nanopore:record-history", args=["zonal_lab", self.lab.pk])
        self.client.force_login(self.make_user("coord_hist", [access.COORDINATOR], zones=[self.zone_a]))
        page = self.client.get(url)
        self.assertContains(page, "Checked against the register")
        self.assertContains(page, "Before")
        self.assertContains(page, "After")
        self.client.force_login(self.make_user("coord_b", [access.COORDINATOR], zones=[self.zone_b]))
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.make_user("nurse_hist", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_starting_point_is_labelled(self):
        self.lab.history.all().delete()
        history.record_starting_points()
        entry = self.lab.history.get()
        self.assertEqual(entry.history_source, history.STARTING_POINT)
        history.record_starting_points()
        self.assertEqual(self.lab.history.count(), 1)  # only once

    def test_tblis_text_values_are_not_changes(self):
        from decimal import Decimal
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(sample_volume=Decimal("2.00"))
        lab = ZonalLaboratory.objects.get(pk=self.lab.pk)
        lab.sample_volume = "2"  # as TB-LIS gives it
        lab.save()
        self.assertEqual(lab.history.count(), 0)
