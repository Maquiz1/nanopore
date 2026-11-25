"""Nanopore runs (20(b)): every attempt kept, the passing run gives the final result."""
from datetime import date

from django.urls import reverse

from nanopore.models import EdcsTblisZonal, NanoporeRun, ZonalLaboratory
from nanopore.models.nanopore_run import FAILED, PASSED
from nanopore.nanopore_runs import export_columns
from nanopore.test_data_safety import DataSafetyBase
from options.models import NanoporeSequencingResults
from utils import access


class NanoporeRunsTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        self.mtbc = NanoporeSequencingResults.objects.create(pk=1, name="MTBC detected", value=1)
        self.failed = NanoporeSequencingResults.objects.create(pk=4, name="Failed", value=4)
        self.none_found = NanoporeSequencingResults.objects.create(pk=3, name="No mycobacteria detected", value=3)
        self.lab = ZonalLaboratory.objects.get(pk=self.zonal_labs["A1"].pk)
        self.client.force_login(self.make_user("lab_runs", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        self.url = reverse("nanopore:zonal-lab-section", args=[self.lab.pk, "nanopore"])

    def post(self, runs, existing=0, **answers):
        data = {"runs-TOTAL_FORMS": len(runs), "runs-INITIAL_FORMS": existing, "runs-MIN_NUM_FORMS": 0, "runs-MAX_NUM_FORMS": 1000,
                "nanopore_done": self.yes.pk, "sequencing_delayed": self.no.pk, "reason_for_change": "Run added", **answers}
        for i, run in enumerate(runs):
            data.update({f"runs-{i}-{k}": v for k, v in run.items()})
        return self.client.post(self.url, data)

    def fresh(self):
        return ZonalLaboratory.objects.get(pk=self.lab.pk)

    def test_failed_runs_then_a_pass(self):
        # Run 1 fails: the result is Failed, nothing to analyse yet
        response = self.post([{"run_date": "2025-11-03", "run_number": "28/25", "outcome": FAILED, "failure_reason": "low_dna", "run_id": "FAX123"}])
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["form"].errors)
        lab = self.fresh()
        self.assertEqual((lab.nanopore_results, lab.nanopore_sequencing_date), (self.failed, date(2025, 11, 3)))
        first = NanoporeRun.objects.get()
        self.assertEqual((first.number, first.run_id), (1, "FAX123"))

        # Run 2 passes: its result must be chosen, and the final date is the passing run's
        existing = {"id": first.pk, "zonal_lab": self.lab.pk, "run_date": "2025-11-03", "run_number": "28/25", "outcome": FAILED, "failure_reason": "low_dna"}
        page = self.post([existing, {"run_date": "2025-11-17", "run_number": "30/25", "outcome": PASSED}], existing=1, nanopore_results=self.failed.pk)
        self.assertIn("nanopore_results", page.context["form"].errors)
        response = self.post([existing, {"run_date": "2025-11-17", "run_number": "30/25", "outcome": PASSED}], existing=1, nanopore_results=self.none_found.pk,
                             epi_to_me=self.no.pk, nanopore_sequencing_date="2020-01-01")  # a typed date is ignored
        self.assertEqual(response.status_code, 302)
        lab = self.fresh()
        self.assertEqual((lab.nanopore_results, lab.nanopore_sequencing_date), (self.none_found, date(2025, 11, 17)))
        self.assertEqual([r.number for r in NanoporeRun.objects.all()], [1, 2])
        self.assertEqual(export_columns(lab), [2, date(2025, 11, 3), date(2025, 11, 17)])

    def test_a_failed_run_needs_its_reason_and_yes_needs_a_run(self):
        page = self.post([{"run_date": "2025-11-03", "run_number": "28/26", "outcome": FAILED}])
        errors = page.context["runs_formset"].forms[0].errors
        self.assertIn("failure_reason", errors)
        self.assertIn("run_number", errors)  # 26 is not the run date's year (2025)
        page = self.post([{"run_date": "", "outcome": ""}])
        self.assertTrue(page.context["form"].non_field_errors())  # 20(a) Yes: add the run
        self.assertFalse(NanoporeRun.objects.exists())

    def test_runs_need_yes(self):
        page = self.post([{"run_date": "2025-11-03", "run_number": "28/25", "outcome": PASSED}], nanopore_done=self.no.pk)
        self.assertIn("nanopore_done", page.context["form"].errors)

    def test_ctrl_dar_form_records_runs_too(self):
        dar_lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001")
        self.client.force_login(self.make_user("ctrl_runs", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        self.url = reverse("nanopore:ctrl-dar-nanopore", args=[dar_lab.pk])
        self.assertIn("runs_formset", self.client.get(self.url).context)
        self.post([{"run_date": "2025-11-05", "run_number": "2925", "outcome": FAILED, "failure_reason": "flow_cell"}])
        self.assertEqual(NanoporeRun.objects.get().zonal_lab, dar_lab)

    def test_failed_result_has_no_epi2me_queries(self):
        from reports.services.zonal_dq import get_zonal_counts
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(nanopore_done=self.yes, nanopore_results=self.failed,
                                                              nanopore_sequencing_date=date(2025, 11, 3), sequencing_delayed=self.no)
        stats = get_zonal_counts(self.make_user("admin_runs", [access.ADMIN]), ZonalLaboratory)[0]
        self.assertFalse(stats.get("missing_epi_to_me"))

    def test_runs_export(self):
        from reports.tasks_export_models import export_model_raw_data_task
        import csv
        import os
        import tempfile
        NanoporeRun.objects.create(zonal_lab=self.lab, run_date=date(2025, 11, 3), run_number="28/25", outcome=FAILED, failure_reason="low_dna")
        NanoporeRun.objects.create(zonal_lab=self.lab, run_date=date(2025, 11, 10), run_number="29/25", outcome=PASSED)
        admin = self.make_user("admin_export_runs", [access.ADMIN])
        with tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            result = export_model_raw_data_task.apply(args=["NanoporeRun"], kwargs={"user_id": admin.pk}).get()
            with open(os.path.join(folder, result["file"]), newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual([(r["pid"], r["attempt"], r["run_number"], r["outcome"]) for r in rows],
                         [(self.lab.screening.pid, "1", "28/25", FAILED), (self.lab.screening.pid, "2", "29/25", PASSED)])
