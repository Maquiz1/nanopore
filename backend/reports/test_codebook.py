"""Codebook built live from forms, models and option tables (reports/codebook.py)."""
from django.urls import reverse

from nanopore.test_access import AccessTestBase
from options.models import YesNo
from reports.codebook import CODEBOOK_FORMS, build_codebook, form_codebook
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
