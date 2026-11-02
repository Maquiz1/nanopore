"""Codebook built live from forms, models and option tables (reports/codebook.py)."""
import csv
import io
import os
import tempfile
from datetime import datetime, timezone as dt_timezone
from unittest import mock

from django.urls import reverse

from nanopore.models import ZonalLaboratory
from nanopore.test_access import AccessTestBase
from options.models import CultureMethod, INHResultLPA, YesNo, YesNoNA
from reports.codebook import CODEBOOK_FORMS, build_codebook, form_codebook
from reports.tasks_export_models import export_all_models_combined_task, export_date
from reports.views.list_models.export_model import ExportModelDataView
from utils import access


class CodebookTests(AccessTestBase):
    def test_every_form_builds_with_its_questions(self):
        codebook = build_codebook(list(CODEBOOK_FORMS))
        self.assertEqual([f["key"] for f in codebook["forms"]], list(CODEBOOK_FORMS))
        for form in codebook["forms"]:
            self.assertTrue(form["rows"], form["title"])
            self.assertNotIn("created_by", [r["Variable name"] for r in form["rows"]])

    def test_question_number_split_from_label(self):
        row = next(r for r in form_codebook("zonal_lab") if r["Variable name"] == "date_sputum_received")
        self.assertEqual((row["Q#"], row["Question label"]), ("2", "Date sputum sample received in laboratory"))
        self.assertEqual((row["Type"], row["Required"]), ("Date", "Yes"))

    def test_choices_come_live_from_option_tables(self):
        row = lambda: next(r for r in form_codebook("zonal_lab") if r["Variable name"] == "culture_performed")
        self.assertEqual(row()["Values"], "1=Yes")
        YesNo.objects.filter(value=1).update(name="Yes, performed")
        self.assertEqual(row()["Values"], "1=Yes, performed")

    def test_participant_link_is_not_listed_as_choices(self):
        row = next(r for r in form_codebook("diagnosis") if r["Variable name"] == "screening")
        self.assertEqual(row["Values"], "")
        self.assertTrue(row["Type"].startswith("Link to"))

    def test_downloads(self):
        self.client.force_login(self.make_user("nurse", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(reverse("reports:codebook")).status_code, 200)
        excel = self.client.get(reverse("reports:codebook-download", args=["zonal_lab", "excel"]))
        self.assertEqual(excel.status_code, 200)
        self.assertTrue(excel.content.startswith(b"PK"))  # xlsx is a zip
        pdf = self.client.get(reverse("reports:codebook-download", args=["all", "pdf"]))
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertEqual(self.client.get(reverse("reports:codebook-download", args=["nope", "pdf"])).status_code, 404)

    def test_login_required(self):
        self.assertEqual(self.client.get(reverse("reports:codebook")).status_code, 302)


class DataExportModesTests(AccessTestBase):
    def export(self, mode):
        self.client.force_login(self.make_user(f"stat_{mode}", [access.STATISTICIAN], zones=[self.zone_a]))
        # SQLite can't join all the option tables at once; the production database can
        with mock.patch.object(ExportModelDataView, "_build_select_related", return_value=["screening"]):
            response = self.client.get(reverse("reports:export_data"), {"model": "ZonalLaboratory", "mode": mode})
            rows = list(csv.DictReader(io.StringIO(b"".join(response.streaming_content).decode())))
        return next(r for r in rows if r["pid"] == self.pid("A1"))

    def setUp(self):
        # An option whose row id (3) differs from its codebook code (98)
        option = YesNoNA.objects.create(pk=3, name="N/A", value=98)
        ZonalLaboratory.objects.filter(pk=self.zonal_labs["A1"].pk).update(culture_isolate=option)

    def test_full_gives_code_and_label(self):
        row = self.export("full")
        self.assertEqual((row["culture_isolate"], row["culture_isolate_label"]), ("98", "N/A"))

    def test_codes_are_the_codebook_values_not_row_ids(self):
        row = self.export("values_only")
        self.assertEqual(row["culture_isolate"], "98")
        self.assertNotIn("culture_isolate_label", row)

    def test_labels_only_gives_labels(self):
        row = self.export("labels_only")
        self.assertEqual(row["culture_isolate"], "N/A")
        self.assertNotIn("culture_isolate_label", row)

    def test_multiple_answers_remarks_and_lpa1_inh_are_exported(self):
        lab = ZonalLaboratory.objects.get(pk=self.zonal_labs["A1"].pk)
        first, second = CultureMethod.objects.create(pk=1, name="LJ", value=1), CultureMethod.objects.create(pk=2, name="MGIT", value=2)
        lab.culture_method.set([second, first])
        lab.lpa1_inh.set([INHResultLPA.objects.create(pk=1, name="Detected", value=1)])
        ZonalLaboratory.objects.filter(pk=lab.pk).update(remarks="A remark", phenotypic_date_performed="2025-01-01")
        row = self.export("full")
        self.assertEqual((row["culture_method"], row["culture_method_label"]), ("1;2", "LJ;MGIT"))
        self.assertEqual((row["lpa1_inh"], row["lpa1_inh_label"]), ("1", "Detected"))
        self.assertEqual(row["remarks"], "A remark")
        self.assertNotIn("phenotypic_date_performed", row)
        self.assertEqual(self.export("values_only")["culture_method"], "1;2")
        self.assertIn("first_line_drugs", row)
        self.assertIn("sequencing_delayed_reasons", row)

    def test_combined_export_has_multiple_answers_and_remarks(self):
        lab = ZonalLaboratory.objects.get(pk=self.zonal_labs["A1"].pk)
        lab.culture_method.set([CultureMethod.objects.create(pk=2, name="MGIT", value=2)])
        ZonalLaboratory.objects.filter(pk=lab.pk).update(remarks="Lab remark")
        with tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            user = self.make_user("stat_combined", [access.STATISTICIAN])
            export_all_models_combined_task.apply(kwargs={"filename": "combined.csv", "user_id": user.pk})
            with open(os.path.join(folder, "combined.csv"), encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        row = next(r for r in rows if r["pid"] == self.pid("A1"))
        self.assertEqual((row["culture_method"], row["lab_remarks"]), ("2", "Lab remark"))
        self.assertIn("diseases_medical", row)
        self.assertIn("tb_diagnosed_clinically", row)
        self.assertNotIn("phenotypic_date_performed", row)

    def test_export_date_is_the_date_in_tanzania(self):
        late_evening_utc = datetime(2026, 11, 2, 22, 30, tzinfo=dt_timezone.utc)
        with mock.patch("django.utils.timezone.now", return_value=late_evening_utc):
            self.assertEqual(export_date(), "2026-11-03")

    def test_file_names_carry_the_date(self):
        self.client.force_login(self.make_user("stat_name", [access.STATISTICIAN]))
        with mock.patch("reports.views.list_models.export_model.export_date", return_value="2026-11-03"):
            response = self.client.get(reverse("reports:export_data"), {"model": "Screening", "mode": "values_only"})
        self.assertIn('filename="Screening_2026-11-03.csv"', response["Content-Disposition"])
        with mock.patch("reports.tasks_export_models.export_date", return_value="2026-11-03"), \
                tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            result = export_all_models_combined_task.apply(kwargs={"mode": "zonal", "user_id": 7}).result
        self.assertEqual(result["file"], "all_models_combined_zonal_2026-11-03_u7.csv")
