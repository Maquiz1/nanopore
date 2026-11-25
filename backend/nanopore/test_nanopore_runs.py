"""Nanopore runs: each run answers 20(b)-21(h); the final run's answers are the Zonal Lab's."""
import csv
import os
import tempfile
from datetime import date

from django.urls import reverse

from nanopore.models import EdcsTblisZonal, NanoporeRun, ZonalLaboratory
from nanopore.models.nanopore_run import FAILED, PASSED
from nanopore.nanopore_runs import export_columns
from nanopore.test_data_safety import DataSafetyBase
from options.models import NanoporeSequencingDelayedReasons, NanoporeSequencingResults
from utils import access


class NanoporeRunsBase(DataSafetyBase):
    def setUp(self):
        super().setUp()
        self.mtbc = NanoporeSequencingResults.objects.create(pk=1, name="MTBC detected", value=1)
        self.none_found = NanoporeSequencingResults.objects.create(pk=3, name="No mycobacteria detected", value=3)
        self.failed = NanoporeSequencingResults.objects.create(pk=4, name="Failed", value=4)
        self.stock_out = NanoporeSequencingDelayedReasons.objects.create(pk=1, name="Reagent stock out", value=1)
        self.lab = ZonalLaboratory.objects.get(pk=self.zonal_labs["A1"].pk)
        self.client.force_login(self.make_user("lab_runs", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        self.url = reverse("nanopore:zonal-lab-section", args=[self.lab.pk, "nanopore"])

    def a_run(self, day, number, result, **answers):
        """One run's answers: EPI2ME not used and no delay unless given."""
        return {"run_date": day, "run_number": number, "nanopore_results": result.pk,
                "epi_to_me": self.no.pk, "sequencing_delayed": self.no.pk, **answers}

    def post(self, runs, existing=0, **answers):
        data = {"runs-TOTAL_FORMS": len(runs), "runs-INITIAL_FORMS": existing, "runs-MIN_NUM_FORMS": 0, "runs-MAX_NUM_FORMS": 1000,
                "nanopore_done": self.yes.pk, "reason_for_change": "Run added", **answers}
        for i, run in enumerate(runs):
            for key, value in run.items():
                data[f"runs-{i}-{key}"] = value
        return self.client.post(self.url, data)

    def fresh(self):
        return ZonalLaboratory.objects.get(pk=self.lab.pk)


class NanoporeRunsTests(NanoporeRunsBase):
    def test_failed_runs_then_a_pass(self):
        first = self.a_run("2025-11-03", "28/25", self.failed, failure_reason="low_dna", run_id="FAX123",
                         epi_to_me=self.yes.pk, epi_to_me_date="2025-11-04", epi_to_me_version="EPI2ME 5.1",
                         sequencing_results=self.no.pk)
        response = self.post([first])
        self.assertEqual(response.status_code, 302)
        lab = self.fresh()
        # The failed run is the final one so far: its answers are the Zonal Lab's
        self.assertEqual((lab.nanopore_results, lab.nanopore_sequencing_date, lab.epi_to_me_version),
                         (self.failed, date(2025, 11, 3), "EPI2ME 5.1"))
        saved = NanoporeRun.objects.get()
        self.assertEqual((saved.number, saved.outcome, saved.run_id), (1, FAILED, "FAX123"))

        # Run 2 passes, after a delay: its answers replace the final ones; run 1 keeps its own
        second = self.a_run("2025-11-17", "30/25", self.none_found, sequencing_delayed=self.yes.pk,
                          sequencing_delayed_days="7", sequencing_delayed_reasons=[self.stock_out.pk])
        response = self.post([{**first, "id": saved.pk, "zonal_lab": self.lab.pk}, second], existing=1,
                             nanopore_sequencing_date="2020-01-01")  # typed answers above the runs are ignored
        self.assertEqual(response.status_code, 302)
        lab = self.fresh()
        self.assertEqual((lab.nanopore_results, lab.nanopore_sequencing_date, lab.epi_to_me, lab.sequencing_delayed_days),
                         (self.none_found, date(2025, 11, 17), self.no, 7))
        self.assertEqual(list(lab.sequencing_delayed_reasons.all()), [self.stock_out])
        runs = list(NanoporeRun.objects.all())
        self.assertEqual([(r.number, r.outcome) for r in runs], [(1, FAILED), (2, PASSED)])
        self.assertEqual(runs[0].epi_to_me_version, "EPI2ME 5.1")
        self.assertEqual(export_columns(lab), [2, date(2025, 11, 3), date(2025, 11, 17), "", ""])  # + no re-run planned, reason

    def test_each_run_is_checked(self):
        page = self.post([self.a_run("2025-11-03", "28/26", self.failed, epi_to_me=self.yes.pk, sequencing_delayed=self.yes.pk)])
        errors = page.context["runs_formset"].forms[0].errors
        for name in ("run_number", "failure_reason", "epi_to_me_date", "epi_to_me_version", "sequencing_results",
                     "sequencing_delayed_days", "sequencing_delayed_reasons"):
            self.assertIn(name, errors)
        self.assertFalse(NanoporeRun.objects.exists())

    def test_yes_needs_a_run_and_runs_need_yes(self):
        page = self.post([{"run_date": "", "run_number": ""}])
        self.assertTrue(page.context["form"].non_field_errors())
        page = self.post([self.a_run("2025-11-03", "28/25", self.none_found)], nanopore_done=self.no.pk)
        self.assertIn("nanopore_done", page.context["form"].errors)

    def test_mtbc_opens_22_once_for_the_final_run(self):
        page = self.post([self.a_run("2025-11-03", "28/25", self.mtbc)])
        self.assertIn("nano_rifampicin", page.context["form"].errors)  # 22 is answered on the section

    def test_an_emptied_run_is_ignored(self):
        response = self.post([self.a_run("2025-11-03", "28/25", self.none_found),
                              {"run_date": "", "run_number": "", "nanopore_results": "", "epi_to_me": "", "sequencing_delayed": ""}])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NanoporeRun.objects.count(), 1)

    def test_ctrl_dar_form_records_runs_too(self):
        dar_lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001")
        self.client.force_login(self.make_user("ctrl_runs", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        self.url = reverse("nanopore:ctrl-dar-nanopore", args=[dar_lab.pk])
        self.assertIn("runs_formset", self.client.get(self.url).context)
        self.assertEqual(self.post([self.a_run("2025-11-05", "2925", self.failed, failure_reason="flow_cell")]).status_code, 302)
        run = NanoporeRun.objects.get()
        self.assertEqual((run.zonal_lab, run.run_number), (dar_lab, "29/25"))

    def test_runs_export(self):
        from reports.tasks_export_models import export_model_raw_data_task
        NanoporeRun.objects.create(zonal_lab=self.lab, run_date=date(2025, 11, 3), run_number="28/25", outcome=FAILED,
                                   failure_reason="low_dna", nanopore_results=self.failed)
        NanoporeRun.objects.create(zonal_lab=self.lab, run_date=date(2025, 11, 10), run_number="29/25", outcome=PASSED,
                                   nanopore_results=self.none_found)
        admin = self.make_user("admin_export_runs", [access.ADMIN])
        with tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            result = export_model_raw_data_task.apply(args=["NanoporeRun"], kwargs={"user_id": admin.pk}).get()
            with open(os.path.join(folder, result["file"]), newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual([(r["pid"], r["attempt"], r["run_number"], r["outcome"], r["nanopore_results"]) for r in rows],
                         [(self.lab.screening.pid, "1", "28/25", FAILED, "4"), (self.lab.screening.pid, "2", "29/25", PASSED, "3")])


class SectionLayoutTests(NanoporeRunsBase):
    def test_only_20a_the_runs_and_22_are_on_the_page(self):
        html = self.client.get(self.url).content.decode()
        self.assertIn("Sequencing runs", html)
        self.assertNotIn('name="nanopore_sequencing_date"', html)
        self.assertNotIn('name="epi_to_me"', html)
        self.assertNotIn('name="nanopore_results"', html)
        self.assertNotIn('name="sequencing_delayed"', html)
        self.assertIn('name="nano_rifampicin"', html)  # 22, once, for the final run

    def test_an_older_record_needs_its_run_and_gets_it_prefilled(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(
            nanopore_done=self.yes, nanopore_sequencing_date=date(2025, 6, 1), epi_to_me=self.no,
            nanopore_results=self.none_found, sequencing_delayed=self.no)
        # The first run card starts from the saved answers
        initial = self.client.get(self.url).context["runs_formset"].forms[0].initial
        self.assertEqual((initial["run_date"], initial["nanopore_results"], initial["epi_to_me"]),
                         (date(2025, 6, 1), self.none_found.pk, self.no.pk))
        # Saving with no run (the card left as it was) is refused: Yes needs its run
        page = self.post([], reason_for_change="Checked")
        self.assertTrue(page.context["form"].non_field_errors())
        # With the run number added, it saves as run 1 and the answers stay
        response = self.post([self.a_run("2025-06-01", "12/25", self.none_found)], reason_for_change="Run entered")
        self.assertEqual(response.status_code, 302)
        lab = self.fresh()
        self.assertEqual((lab.nanopore_sequencing_date, lab.nanopore_results, lab.nanopore_runs.count()),
                         (date(2025, 6, 1), self.none_found, 1))


class CtrlViewTests(NanoporeRunsBase):
    def test_dar_nanopore_card_has_a_read_only_view(self):
        dar_lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001")
        self.client.force_login(self.make_user("ctrl_view", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        view = reverse("nanopore:ctrl-dar-nanopore", args=[dar_lab.pk]) + "?view=1"
        self.assertContains(self.client.get(reverse("nanopore:zonal-lab-hub", args=[dar_lab.pk])), view)
        page = self.client.get(view)
        self.assertTrue(page.context["read_only"])
        self.assertTrue(all(f.disabled for f in page.context["form"].fields.values()))
        self.assertNotContains(page, "fa-floppy-disk")


class BackAfterSaveTests(NanoporeRunsBase):
    def test_save_returns_to_the_page_the_user_came_from(self):
        came_from = reverse("reports:ctrl_dar_work") + "?tab=nanopore"
        page = self.client.get(self.url, HTTP_REFERER="http://testserver" + came_from)
        self.assertEqual(page.context["next"], "http://testserver" + came_from)  # kept in the form
        response = self.post([self.a_run("2025-11-03", "28/25", self.none_found)], next=page.context["next"])
        self.assertRedirects(response, "http://testserver" + came_from, fetch_redirect_response=False)

    def test_other_sites_and_the_form_itself_are_not_followed(self):
        self.assertIsNone(self.client.get(self.url, HTTP_REFERER="https://example.org/x").context["next"] or None)
        self.assertIsNone(self.client.get(self.url, HTTP_REFERER="http://testserver" + self.url).context["next"] or None)


class ReasonForChangeTests(NanoporeRunsBase):
    """Changing or removing a saved run needs a reason, like any saved answer; a new run doesn't."""

    def test_changing_a_saved_run_needs_a_reason(self):
        first = self.a_run("2025-11-03", "28/25", self.none_found)
        self.assertEqual(self.post([first]).status_code, 302)  # a first entry needs no reason
        saved = NanoporeRun.objects.get()
        changed = {**first, "id": saved.pk, "zonal_lab": self.lab.pk, "run_number": "29/25"}
        page = self.post([changed], existing=1, reason_for_change="")
        self.assertIn("reason_for_change", page.context["form"].errors)
        removed = {**first, "id": saved.pk, "zonal_lab": self.lab.pk, "DELETE": "on"}
        page = self.post([removed, self.a_run("2025-11-05", "30/25", self.none_found)], existing=1, reason_for_change="")
        self.assertIn("reason_for_change", page.context["form"].errors)
        response = self.post([changed], existing=1, reason_for_change="Run number typed wrongly")
        self.assertEqual(response.status_code, 302)
        run = NanoporeRun.objects.get()
        self.assertEqual((run.run_number, run.history.first().history_change_reason), ("29/25", "Run number typed wrongly"))

    def test_adding_a_run_needs_no_reason(self):
        first = self.a_run("2025-11-03", "28/25", self.failed, failure_reason="low_dna")
        self.post([first])
        saved = NanoporeRun.objects.get()
        response = self.post([{**first, "id": saved.pk, "zonal_lab": self.lab.pk}, self.a_run("2025-11-10", "29/25", self.none_found)],
                             existing=1, reason_for_change="")
        self.assertEqual(response.status_code, 302)


class RegimenReasonTests(DataSafetyBase):
    def test_correcting_a_saved_regimen_row_needs_a_reason(self):
        from nanopore.models import RegimenChanges
        row = RegimenChanges.objects.create(screening=self.screenings["A1"], date=date(2025, 5, 1), drug="RHZE")
        self.client.force_login(self.make_user("ds_reg", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        url = reverse("nanopore:regimen-save")
        response = self.client.post(url, {"regimen_id": row.pk, "date": "2025-05-01", "drug": "RH"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("reason_for_change", response.json()["errors"])
        response = self.client.post(url, {"regimen_id": row.pk, "date": "2025-05-01", "drug": "RH", "reason_for_change": "Typed wrongly"})
        self.assertEqual(response.status_code, 200)
        row.refresh_from_db()
        self.assertEqual((row.drug, row.history.first().history_change_reason), ("RH", "Typed wrongly"))


class NanoporeFailedListTests(NanoporeRunsBase):
    """Nanopore failed (info): every run failed so far; leaves the list when a re-run has a result."""

    def test_listed_until_a_run_has_a_result(self):
        url = reverse("reports:nanopore_failed")
        self.client.force_login(self.make_user("ds_nf", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        self.assertEqual(self.client.get(url).context["page_obj"].paginator.count, 0)
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(nanopore_done=self.yes, nanopore_results=self.failed,
                                                              nanopore_sequencing_date=date(2025, 11, 3))
        NanoporeRun.objects.create(zonal_lab=self.lab, run_date=date(2025, 11, 3), run_number="28/25", outcome=FAILED,
                                   failure_reason="low_dna", nanopore_results=self.failed)
        from django.core.cache import cache
        cache.clear()  # the sidebar badge is cached for a few minutes
        page = self.client.get(url)
        row = page.context["rows"][0]
        self.assertEqual((row["lab"].pk, row["lab"].runs, row["last"].run_number), (self.lab.pk, 1, "28/25"))
        self.assertEqual(page.context["context_nanopore_failed_total"], 1)
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(nanopore_results=self.none_found)
        self.assertEqual(self.client.get(url).context["page_obj"].paginator.count, 0)
        self.client.force_login(self.make_user("nurse_nf", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(url).status_code, 403)


class NanoporeFailedTabsTests(NanoporeRunsBase):
    def setUp(self):
        super().setUp()
        from django.core.cache import cache
        cache.clear()
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(nanopore_done=self.yes, nanopore_results=self.failed,
                                                              nanopore_sequencing_date=date(2025, 3, 5))
        self.url = reverse("reports:nanopore_failed")

    def counts(self):
        return {t["key"]: t["count"] for t in self.client.get(self.url).context["tabs"]}

    def test_before_runs_then_no_rerun_planned_then_undo(self):
        self.client.force_login(self.make_user("lab_nf", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        self.client.logout()
        self.client.force_login(self.make_user("ds_nf2", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        self.assertEqual(self.counts(), {"since": 0, "before": 1, "closed": 0})
        # A reason is needed
        self.client.post(self.url, {"lab": self.lab.pk, "action": "close", "reason": ""})
        self.assertFalse(self.fresh().nanopore_rerun_not_planned)
        self.client.post(self.url, {"lab": self.lab.pk, "action": "close", "reason": "No sample left"})
        lab = self.fresh()
        self.assertEqual((lab.nanopore_rerun_not_planned, lab.nanopore_rerun_not_planned_reason), (True, "No sample left"))
        self.assertEqual(lab.history.first().history_change_reason, "No re-run planned: No sample left")
        self.assertEqual(self.counts(), {"since": 0, "before": 0, "closed": 1})
        self.client.post(self.url, {"lab": self.lab.pk, "action": "reopen"})
        self.assertEqual(self.counts(), {"since": 0, "before": 1, "closed": 0})

    def test_read_only_roles_cannot_close_and_filters_work(self):
        self.client.force_login(self.make_user("stat_nf", [access.STATISTICIAN], zones=[self.zone_a]))
        page = self.client.get(self.url, {"tab": "before"})
        self.assertFalse(page.context["rows"][0]["may_close"])
        self.assertEqual(self.client.post(self.url, {"lab": self.lab.pk, "action": "close", "reason": "x"}).status_code, 403)
        self.assertEqual(self.client.get(self.url, {"tab": "before", "site": self.a1.pk}).context["page_obj"].paginator.count, 1)
        self.assertEqual(self.client.get(self.url, {"tab": "before", "zone": self.zone_b.pk}).context["page_obj"].paginator.count, 1)  # not one of theirs: ignored
