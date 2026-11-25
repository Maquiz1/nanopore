"""Query lists, CTRL isolate queries, exports and MGIT text (items 6 and 8-14 of the November review)."""
import csv
import io
import os
import tempfile
from datetime import date
from decimal import Decimal
from unittest import mock

from django.test import Client
from django.urls import reverse

from nanopore.models import EdcsTblisMismatch, EdcsTblisZonal, RegimenChanges, Screening, ZonalLaboratory
from nanopore.tasks_tblis_raw import mgit_result_value, process_raw_tblis_upload
from nanopore.test_data_safety import DataSafetyBase
from options.models import YesNoNA
from reports.services.zonal_dq import get_ctrl_isolate_counts
from reports.services.zonal_dq.problem_lists import get_zonal_problem_lists
from reports.tasks_export_models import export_all_models_combined_task
from reports.views.list_models.export_model import ExportModelDataView
from utils import access


class QueryListTests(DataSafetyBase):
    def test_every_record_of_a_query_is_listed(self):
        for i in range(15):
            screening = Screening.objects.create(screening_date=date(2025, 3, 1), pid1=f"1{i:02}", pid2=f"1{i:02}",
                                                 site=self.dar_site, eligible=True)
            EdcsTblisZonal.objects.create(screening=screening, unique_lab_no=f"D{i}")
        lists = get_zonal_problem_lists(EdcsTblisZonal.objects.all(), [])
        self.assertEqual(len(lists["missing_date_sputum_received"]), 15)


class CtrlIsolateQueryTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        self.admin = self.make_user("admin_iso", [access.ADMIN])
        self.lab = self.zonal_labs["B1"]
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(
            culture_isolate=YesNoNA.objects.create(pk=1, name="Yes", value=1), isolate_unique_lab_no="50001",
            isolate_date=date(2025, 5, 1))

    def complete(self):
        self.client.force_login(self.admin)
        page = self.client.get(reverse("reports:ctrl_isolates"), {"tab": "complete"})
        return self.lab.pk in [row["z"].pk for row in page.context["rows"]]

    def test_dst_no_is_waiting_for_dst_not_a_query(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(phenotypic_performed=self.no)
        self.assertNotIn("missing_phenotypic_performed", get_ctrl_isolate_counts(self.admin))  # information (D06)
        self.assertFalse(self.complete())
        page = self.client.get(reverse("reports:ctrl_isolates"), {"tab": "waiting-dst"})
        self.assertIn(self.lab.pk, [row["z"].pk for row in page.context["rows"]])

    def test_dst_yes_is_complete(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(phenotypic_performed=self.yes, first_line_dst_performed=self.no,
                                                              second_line_dst_performed=self.no)
        self.assertTrue(self.complete())

    def test_form_says_where_the_dst_comes_from(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(phenotypic_performed=self.no, isolate_unique_lab_no=None)
        self.client.force_login(self.make_user("ctrl_text", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        url = reverse("nanopore:ctrl-isolate-update", args=[self.lab.pk])
        self.assertContains(self.client.get(url), "Answered by the site")
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(isolate_unique_lab_no="50001")
        self.assertContains(self.client.get(url), "From the TB-LIS upload")


class ExportValueTests(DataSafetyBase):
    def export(self, model, mode="values_only"):
        self.client.force_login(self.make_user(f"stat_{model}_{mode}", [access.STATISTICIAN]))
        # SQLite can't join all the option tables at once; the production database can
        with mock.patch.object(ExportModelDataView, "_build_select_related", return_value=[]):
            response = self.client.get(reverse("reports:export_data"), {"model": model, "mode": mode})
            return list(csv.reader(io.StringIO(b"".join(response.streaming_content).decode())))

    def test_zero_is_exported(self):
        ZonalLaboratory.objects.filter(pk=self.zonal_labs["A1"].pk).update(sample_volume=Decimal("0"))
        header, *rows = self.export("ZonalLaboratory")
        row = next(r for r in rows if r[0] == self.pid("A1"))
        self.assertEqual(Decimal(row[header.index("sample_volume")]), 0)

    def test_one_row_per_regimen_change(self):
        screening = self.screenings["A1"]
        for day in (1, 2):
            RegimenChanges.objects.create(screening=screening, date=date(2025, 5, day), drug=f"Drug {day}")
        header, *rows = self.export("Screening")
        self.assertEqual({len(row) for row in rows}, {len(header)})
        mine = [row for row in rows if row[header.index("pid")] == screening.pid]
        self.assertEqual([row[header.index("regimen_drug")] for row in mine], ["Drug 1", "Drug 2"])
        self.assertEqual(len([row for row in rows if row[header.index("pid")] == self.pid("A2")]), 1)

    def test_combined_column_names_are_unique(self):
        with tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            user = self.make_user("stat_names", [access.STATISTICIAN])
            export_all_models_combined_task.apply(kwargs={"filename": "c.csv", "user_id": user.pk}).get()
            with open(os.path.join(folder, "c.csv"), encoding="utf-8") as handle:
                header = next(csv.reader(handle))
        self.assertEqual(len(header), len(set(header)))
        self.assertIn("enrollment_tb_regimen", header)
        self.assertIn("diagnosis_tb_regimen", header)
        self.assertNotIn("tb_regimen", header)


class MgitTextTests(DataSafetyBase):
    def test_negated_or_unknown_text_is_not_read_as_a_result(self):
        for text, value in (("No colonies seen", None), ("NIL colonies", None), ("0 colonies", None), ("Something new", None),
                            ("3 Colonies", 1), ("POSITIVE", 1), ("NEGATIVE", 2), ("Contaminated", 3), ("POSITIVE FOR NTM", 4)):
            self.assertEqual(mgit_result_value(text), value, text)

    def test_unrecognised_text_is_listed_for_checking(self):
        ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        csv.writer(handle).writerows([["labno", "spectype", "peripheralres_genexpert", "mgit_res"],
                                      ["30001", "Sputum", "MTB Detected", "No colonies seen"]])
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        process_raw_tblis_upload.apply(args=[handle.name, None, "t.csv"]).get()
        self.assertIsNone(EdcsTblisZonal.objects.get(screening=self.dar).mgit_results)
        self.assertTrue(EdcsTblisMismatch.objects.filter(field_name="mgit_results (unrecognised TBLIS value)").exists())


class ExportRequestTests(DataSafetyBase):
    def test_export_request_needs_the_page_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.make_user("ds_csrf", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        url = reverse("nanopore:edcs-tblis-export-trigger")
        with mock.patch("nanopore.views.laboratory.edcs_tblis.edcs_tblis_csv_export_views.export_edcs_tblis_csv.delay") as delay:
            delay.return_value.id = "task"
            self.assertEqual(client.post(url, "{}", content_type="application/json").status_code, 403)
            page = client.get(reverse("nanopore:edcs-tblis-laboratory-list"))
            token = page.cookies["csrftoken"].value
            self.assertEqual(client.post(url, "{}", content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)


class NoDstPageTests(DataSafetyBase):
    """Positive culture, no DST: its own page above TB-LIS follow-up, for information."""

    def test_page_lists_both_groups_and_stays_out_of_the_totals(self):
        from nanopore.models import EdcsTblisZonal, ZonalLaboratory
        from options.models import MGITCultureResult, YesNoNA
        positive = MGITCultureResult.objects.create(pk=1, name="Positive", value=1)
        ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001", mgit_results=positive)
        ZonalLaboratory.objects.filter(pk=self.zonal_labs["B1"].pk).update(
            culture_isolate=YesNoNA.objects.create(pk=1, name="Yes", value=1), isolate_unique_lab_no="50001")
        self.client.force_login(self.make_user("ds_nodst", [access.ADMIN]))
        page = self.client.get(reverse("reports:no_dst"))
        self.assertEqual({g["key"]: g["count"] for g in page.context["groups"]}, {"dar": 1, "others": 1})
        self.assertEqual(page.context["context_no_dst_total"], 2)
        self.assertContains(page, reverse("reports:no_dst"))  # in the sidebar
        self.client.force_login(self.make_user("nurse_nodst", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(reverse("reports:no_dst")).status_code, 403)
