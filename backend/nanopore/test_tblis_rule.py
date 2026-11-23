"""What a new TB-LIS file does to results from earlier files (nanopore/tblis_status.py)."""
import csv
import os
import tempfile
from datetime import date
from importlib import import_module
from unittest import mock

from django.apps import apps
from django.urls import reverse

from nanopore import tblis_status
from nanopore.models import (
    EdcsTblisZonal, TblisFollowUp, TblisIsolateDst, TblisLeftOut, TblisRawData, TblisUploadBatch, ZonalLaboratory,
)
from nanopore.recycle_bin import restore, soft_delete
from nanopore.tasks_tblis_raw import process_raw_tblis_upload, sync_zonal_laboratory_daily
from nanopore.test_data_safety import DataSafetyBase
from options.models import MGITCultureResult, PhenotypicDSTResults, YesNoNA
from reports.tasks_export_models import export_all_models_combined_task
from reports.views.list_models.export_model import ExportModelDataView
from utils import access

HEADER = ["labno", "spectype", "peripheralres_genexpert", "rctdate", "mgit_res", "ljdst1_date", "ljdst1_rifampicin", "mgitdst2_ethionamide"]


def sputum(labno="30001", mgit="POSITIVE", genexpert="MTB Detected", spectype="Sputum", dst="2025-06-20"):
    return [labno, spectype, genexpert, "2025-05-15", mgit, dst, "Resistant" if dst else "", ""]


def isolate(labno="50001", dst="2025-06-20", rifampicin="Resistant", ethionamide="", spectype="Isolate"):
    return [labno, spectype, "Not Provided", "2025-05-15", "", dst, rifampicin, ethionamide]


OTHER_ROW = sputum("99999")  # a file that has neither record


class RuleBase(DataSafetyBase):
    def setUp(self):
        super().setUp()
        self.positive = MGITCultureResult.objects.create(pk=1, name="Positive", value=1)
        self.negative = MGITCultureResult.objects.create(pk=2, name="Negative", value=2)
        self.resistant = PhenotypicDSTResults.objects.create(pk=1, name="Resistant", value=1)
        self.susceptible = PhenotypicDSTResults.objects.create(pk=2, name="Susceptible", value=2)
        self.dar_lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001", remarks="CTRL remark", nanopore_done=self.no)
        self.other = self.zonal_labs["B1"]

    def upload(self, *rows, dry_run=False):
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        csv.writer(handle).writerows([HEADER, *rows])
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return process_raw_tblis_upload.apply(args=[handle.name, None, "test.csv"], kwargs={"dry_run": dry_run}).get()

    def nightly(self):
        sync_zonal_laboratory_daily.apply().get()

    def edcs(self, lab=None):
        return EdcsTblisZonal.objects.get(screening=(lab or self.dar_lab).screening)

    def state(self, labno="30001", isolate=False):
        return tblis_status.status(labno, isolate).state


class DarRuleTests(RuleBase):
    def test_rejected_in_the_new_file_removes_only_tblis_values(self):
        for change in ({"genexpert": "MTB Not Detected"}, {"genexpert": ""}, {"spectype": ""}, {"spectype": "Urine"}):
            self.upload(sputum())
            self.assertEqual(self.edcs().mgit_results, self.positive)
            self.upload(sputum(**change))
            record = self.edcs()
            self.assertIsNone(record.mgit_results, change)
            self.assertIsNone(record.rifampicin, change)
            self.assertEqual((record.remarks, record.nanopore_done), ("CTRL remark", self.no))
            self.nightly()
            self.assertIsNone(self.edcs().mgit_results, change)
            self.assertEqual(self.state(), tblis_status.REJECTED)

    def test_rejected_gives_back_the_zonal_value(self):
        ZonalLaboratory.objects.filter(pk=self.dar_lab.pk).update(mgit_results=self.negative)
        self.upload(sputum())
        self.assertEqual(self.edcs().mgit_results, self.positive)
        self.upload(sputum(genexpert="MTB Not Detected"))
        self.assertEqual(self.edcs().mgit_results, self.negative)
        self.assertEqual(ZonalLaboratory.objects.get(pk=self.dar_lab.pk).mgit_results, self.negative)

    def test_absent_from_the_new_file_keeps_the_last_accepted_result(self):
        self.upload(sputum())
        self.assertEqual(self.state(), tblis_status.CURRENT)
        self.upload(OTHER_ROW)
        self.assertEqual(self.edcs().mgit_results, self.positive)
        self.nightly()
        self.assertEqual(self.edcs().mgit_results, self.positive)
        self.assertEqual(self.state(), tblis_status.NOT_IN_LATEST)

    def test_absent_after_a_rejection_stays_rejected(self):
        self.upload(sputum())
        self.upload(sputum(genexpert="MTB Not Detected"))
        self.upload(OTHER_ROW)
        self.nightly()
        self.assertIsNone(self.edcs().mgit_results)
        self.assertEqual(self.state(), tblis_status.REJECTED)

    def test_accepted_again_comes_back(self):
        self.upload(sputum(genexpert=""))
        self.upload(sputum())
        self.assertEqual((self.edcs().mgit_results, self.state()), (self.positive, tblis_status.CURRENT))

    def test_an_accepted_row_wins_over_a_rejected_one_in_the_same_file(self):
        self.upload(sputum(), sputum(genexpert="MTB Not Detected"))
        self.nightly()
        self.assertEqual((self.edcs().mgit_results, self.state()), (self.positive, tblis_status.CURRENT))
        self.assertFalse(TblisLeftOut.objects.filter(labno="30001").exists())

    def test_rows_older_uploads_stored_though_rejected_are_not_used(self):
        TblisRawData.objects.create(labno="30001", raw_data={
            "spectype": "Sputum", "peripheralres_genexpert": "MTB Not Detected", "mgit_res": "POSITIVE"})
        self.nightly()
        self.assertIsNone(self.edcs().mgit_results)
        self.assertEqual(self.state(), tblis_status.REJECTED)

    def test_an_isolate_row_is_not_a_sighting_of_the_sputum(self):
        self.upload(sputum())
        self.upload(isolate("30001"))
        self.nightly()
        self.assertEqual((self.edcs().mgit_results, self.state()), (self.positive, tblis_status.NOT_IN_LATEST))

    def test_preview_counts_what_would_be_removed_and_saves_nothing(self):
        self.upload(sputum())
        result = self.upload(sputum(genexpert="MTB Not Detected"), dry_run=True)
        self.assertEqual((result["results_removed"], result["not_in_latest_count"]), (1, 0))
        self.assertEqual(self.edcs().mgit_results, self.positive)
        self.assertFalse(TblisLeftOut.objects.exists())
        self.assertEqual(self.upload(OTHER_ROW, dry_run=True)["not_in_latest_count"], 1)

    def test_repeating_the_same_file_changes_nothing(self):
        self.upload(sputum())
        before = self.edcs().mgit_results, self.edcs().rifampicin
        self.assertEqual(self.upload(sputum())["results_removed"], 0)
        self.assertEqual((self.edcs().mgit_results, self.edcs().rifampicin), before)


class IsolateRuleTests(RuleBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.make_user("ctrl_rule", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        ZonalLaboratory.objects.filter(pk=self.other.pk).update(culture_isolate=YesNoNA.objects.create(pk=1, name="Yes", value=1))

    def enter(self, number="50001"):
        response = self.client.post(reverse("nanopore:ctrl-isolate-update", args=[self.other.pk]), {"isolate_unique_lab_no": number})
        self.assertEqual(response.status_code, 302)

    def site_has(self, **values):
        ZonalLaboratory.objects.filter(pk=self.other.pk).update(**values)

    def both(self):
        return ZonalLaboratory.objects.get(pk=self.other.pk), self.edcs(self.other)

    def test_blank_removes_what_tblis_gave(self):
        self.enter()
        self.upload(isolate())
        self.assertEqual(self.both()[0].rifampicin, self.resistant)
        self.upload(isolate(dst="", rifampicin=""))
        for record in self.both():
            self.assertEqual(record.phenotypic_performed, None)  # 12a: empty without a DST date
            self.assertIsNone(record.rifampicin)
            self.assertIsNone(record.first_line_dst_results_date)

    def test_blank_gives_back_what_the_site_entered(self):
        self.site_has(rifampicin=self.susceptible, phenotypic_performed=self.yes, phenotypic_date_performed=date(2025, 1, 9))
        self.enter()
        self.upload(isolate())
        self.assertEqual(self.both()[0].rifampicin, self.resistant)
        self.upload(isolate(dst="", rifampicin=""))
        for record in self.both():
            self.assertEqual((record.rifampicin, record.phenotypic_performed, record.phenotypic_date_performed),
                             (self.susceptible, self.yes, date(2025, 1, 9)))

    def test_same_as_the_sites_value_is_still_the_sites(self):
        self.site_has(rifampicin=self.resistant)
        self.enter()
        self.upload(isolate())
        self.upload(isolate(dst="", rifampicin=""))
        self.assertEqual(self.both()[0].rifampicin, self.resistant)

    def test_a_later_site_edit_is_not_removed(self):
        self.enter()
        self.upload(isolate(ethionamide="Resistant"))
        self.assertEqual(self.both()[0].ethionamide, self.resistant)
        self.site_has(ethionamide=self.susceptible)
        self.upload(isolate())
        self.assertEqual(self.both()[0].ethionamide, self.susceptible)

    def test_absent_keeps_the_dst_and_is_marked(self):
        self.enter()
        self.upload(isolate())
        self.upload(OTHER_ROW)
        self.nightly()
        self.assertEqual(self.both()[1].rifampicin, self.resistant)
        self.assertEqual(self.state("50001", True), tblis_status.NOT_IN_LATEST)

    def test_no_longer_an_isolate_removes_the_dst(self):
        self.enter()
        self.upload(isolate())
        result = self.upload(isolate(spectype=""))
        for record in self.both():
            self.assertIsNone(record.rifampicin)
            self.assertIsNone(record.phenotypic_performed)
        self.assertEqual((result["results_removed"], self.state("50001", True)), (1, tblis_status.REJECTED))

    def test_changing_the_number_gives_back_the_sites_values(self):
        self.site_has(rifampicin=self.susceptible, ethionamide=self.susceptible)
        self.enter()
        self.upload(isolate(ethionamide="Resistant"))
        self.enter("50009")
        for record in self.both():
            self.assertEqual((record.rifampicin, record.ethionamide), (self.susceptible, self.susceptible))
            self.assertIsNone(record.phenotypic_performed)

    def test_dst_merged_before_this_was_recorded_can_still_be_removed(self):
        self.site_has(isolate_unique_lab_no="50001")
        self.upload(isolate())
        TblisIsolateDst.objects.all().delete()  # as if merged by the earlier code
        self.upload(isolate(dst="", rifampicin=""))
        self.assertIsNone(self.both()[0].rifampicin)
        self.assertIsNone(self.both()[0].phenotypic_performed)  # 12a: empty without a DST date

    def test_dst_merged_before_with_no_stored_row_is_left_alone(self):
        self.site_has(isolate_unique_lab_no="50001", rifampicin=self.resistant)
        self.upload(isolate(dst="", rifampicin=""))
        self.assertEqual(self.both()[0].rifampicin, self.resistant)

    def test_nightly_again_changes_nothing(self):
        self.enter()
        self.upload(isolate())
        values = TblisIsolateDst.objects.get().values
        self.nightly()
        self.nightly()
        self.assertEqual(TblisIsolateDst.objects.get().values, values)
        self.assertEqual(self.both()[1].rifampicin, self.resistant)

    def test_recycle_bin_brings_the_record_of_what_tblis_gave_back(self):
        self.enter()
        self.upload(isolate())
        user = self.make_user("admin_rule", [access.ADMIN])
        entry = soft_delete(self.other.screening, user)
        self.assertFalse(TblisIsolateDst.objects.exists())
        restore(entry, user)
        self.assertEqual(TblisIsolateDst.objects.get().number, "50001")


class StatusShownTests(RuleBase):
    def combined(self):
        user = self.make_user(f"stat_{TblisUploadBatch.objects.count()}", [access.STATISTICIAN])
        with tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            export_all_models_combined_task.apply(kwargs={"mode": "edcs", "filename": "c.csv", "user_id": user.pk}).get()
            with open(os.path.join(folder, "c.csv"), encoding="utf-8") as handle:
                return next(row for row in csv.DictReader(handle) if row["pid"] == self.dar.pid)

    def test_combined_export_marks_each_state(self):
        self.upload(sputum())
        row = self.combined()
        self.assertEqual((row["mgit_results"], row["tblis_status"]), ("1", "In latest file"))
        self.upload(OTHER_ROW)
        row = self.combined()
        self.assertEqual((row["mgit_results"], row["tblis_status"]), ("1", "Not in latest file"))
        self.upload(sputum(genexpert=""))
        row = self.combined()
        self.assertEqual((row["mgit_results"], row["tblis_status"], row["lab_remarks"]), ("", "Rejected in TB-LIS", "CTRL remark"))

    def test_per_form_export_has_the_status(self):
        self.upload(sputum())
        self.client.force_login(self.make_user("stat_form", [access.STATISTICIAN]))
        # SQLite can't join all the option tables at once; the production database can
        with mock.patch.object(ExportModelDataView, "_build_select_related", return_value=["screening"]):
            response = self.client.get(reverse("reports:export_data"), {"model": "EdcsTblisZonal", "mode": "values_only"})
            rows = list(csv.DictReader(b"".join(response.streaming_content).decode().splitlines()))
        self.assertEqual(next(r for r in rows if r["pid"] == self.dar.pid)["tblis_status"], "In latest file")

    def test_follow_up_lists_rejected_and_absent(self):
        url = reverse("nanopore:tblis-follow-up")
        self.client.force_login(self.make_user("rev_rule", [access.REVIEWER]))
        self.upload(sputum())
        self.upload(OTHER_ROW)
        self.assertContains(self.client.get(url, {"list": "absent"}), self.dar.pid)
        self.assertNotContains(self.client.get(url, {"list": "rejected"}), self.dar.pid)
        self.upload(sputum(genexpert="MTB Not Detected"))
        page = self.client.get(url, {"list": "rejected"})
        self.assertContains(page, self.dar.pid)
        self.assertContains(page, "GeneXpert: MTB Not Detected")
        self.assertNotContains(self.client.get(url, {"list": "absent"}), self.dar.pid)

    def test_follow_up_lists_follow_the_assignment(self):
        self.upload(sputum())
        self.upload(OTHER_ROW)
        self.client.force_login(self.make_user("ds_rule", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        self.assertNotContains(self.client.get(reverse("nanopore:tblis-follow-up"), {"list": "absent"}), self.dar.pid)

    def test_edcs_record_says_it_is_not_in_the_latest_file(self):
        self.upload(sputum())
        self.upload(OTHER_ROW)
        self.client.force_login(self.make_user("rev_view", [access.REVIEWER]))
        self.assertContains(self.client.get(reverse("nanopore:edcs-tblis-laboratory-view", args=[self.edcs().pk])), "Not in latest file")

    def test_migration_remembers_the_latest_follow_up_rejections(self):
        batch = TblisUploadBatch.objects.create(source_file_name="t.csv")
        TblisFollowUp.objects.create(labno="30001", reason="genexpert_missing", upload_batch=batch)
        TblisFollowUp.objects.create(labno="30002", reason="genexpert_missing", upload_batch=batch)
        TblisRawData.objects.create(labno="30002", upload_batch=batch, raw_data={})  # also had a row that was used
        import_module("nanopore.migrations.0052_tblis_left_out_isolate_dst").remember_left_out(apps, None)
        self.assertEqual(list(TblisLeftOut.objects.values_list("labno", "seen_at")), [("30001", batch.created_at)])
