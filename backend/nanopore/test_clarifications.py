"""DST after a No, Dar isolate answers, DST performed dates, and the smaller fixes of 23 Nov."""
import csv
import os
import tempfile
from datetime import date
from unittest import mock

from django.test import Client
from django.urls import reverse

from nanopore.models import EdcsTblisZonal, TblisRawData, TblisUploadBatch, ZonalLaboratory
from nanopore.tasks_tblis_raw import apply_tblis_dst, process_raw_tblis_upload, sync_with_latest_tblis
from nanopore.test_data_safety import DataSafetyBase
from options.models import PhenotypicDSTResults, YesNoNA
from reports.services.zonal_dq import get_ctrl_isolate_counts, get_zonal_counts
from utils import access


class DstAfterNoTests(DataSafetyBase):
    def test_no_more_dst_questions_after_no(self):
        admin = self.make_user("admin_no", [access.ADMIN])
        resistant = PhenotypicDSTResults.objects.create(pk=1, name="Resistant", value=1)
        ZonalLaboratory.objects.filter(pk=self.zonal_labs["B1"].pk).update(
            culture_isolate=YesNoNA.objects.create(pk=1, name="Yes", value=1), isolate_unique_lab_no="50001",
            phenotypic_performed=self.no, first_line_dst_performed=self.yes, rifampicin=resistant)
        counts = get_ctrl_isolate_counts(admin)
        follow_on = {key: n for key, n in counts.items() if n and key != "missing_phenotypic_performed"}
        self.assertEqual(follow_on, {})
        self.assertEqual(counts["missing_phenotypic_performed"], 1)  # the No itself stays a query

    def test_dar_no_more_dst_questions_after_no(self):
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001", phenotypic_performed=self.no,
                                      first_line_dst_performed=self.yes)
        stats = get_zonal_counts(self.make_user("admin_dar", [access.ADMIN]), EdcsTblisZonal)[0]
        for key in ("missing_first_line_dst_performed_date", "missing_first_line_dst_results_date", "missing_first_line_dst_results",
                    "missing_second_line_dst_performed"):
            self.assertFalse(stats.get(key), key)


class DstNeedsIsolateTests(DataSafetyBase):
    """Other zones: DST only for an isolate sent to CTRL. Dar es Salaam: whatever the isolate answer."""

    def test_other_zones_ask_dst_only_for_an_isolate_sent(self):
        admin = self.make_user("admin_iso_dst", [access.ADMIN])
        ZonalLaboratory.objects.filter(pk=self.zonal_labs["B1"].pk).update(
            culture_isolate=YesNoNA.objects.create(pk=2, name="No", value=2), phenotypic_performed=self.yes,
            first_line_dst_performed=self.yes)
        self.assertEqual({k: n for k, n in get_ctrl_isolate_counts(admin).items() if n}, {})
        ZonalLaboratory.objects.filter(pk=self.zonal_labs["B1"].pk).update(culture_isolate=YesNoNA.objects.create(pk=1, name="Yes", value=1))
        counts = get_ctrl_isolate_counts(admin)
        self.assertEqual(counts["missing_first_line_dst_performed_date"], 1)

    def test_dar_asks_dst_whatever_the_isolate_answer(self):
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001", culture_isolate=YesNoNA.objects.create(
            pk=3, name="Na", value=98), phenotypic_performed=self.yes, first_line_dst_performed=self.yes)
        stats = get_zonal_counts(self.make_user("admin_dar_dst", [access.ADMIN]), EdcsTblisZonal)[0]
        self.assertEqual(stats["missing_first_line_dst_performed_date"], 1)


class DarIsolateTests(DataSafetyBase):
    def test_dar_isolate_questions_are_na(self):
        na = YesNoNA.objects.create(pk=3, name="Na", value=98)
        lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001", culture_isolate=YesNoNA.objects.create(
            pk=1, name="Yes", value=1), isolate_date=date(2025, 1, 1))
        record = sync_with_latest_tblis(lab)
        self.assertEqual((record.culture_isolate, record.isolate_date, record.isolate_unique_lab_no), (na, None, None))
        self.assertEqual(ZonalLaboratory.objects.get(pk=lab.pk).isolate_date, date(2025, 1, 1))  # the form itself is left alone

    def test_other_zones_keep_their_answer(self):
        yes = YesNoNA.objects.create(pk=1, name="Yes", value=1)
        YesNoNA.objects.create(pk=3, name="Na", value=98)
        lab = self.zonal_labs["B1"]
        ZonalLaboratory.objects.filter(pk=lab.pk).update(culture_isolate=yes)
        self.assertEqual(sync_with_latest_tblis(ZonalLaboratory.objects.get(pk=lab.pk)).culture_isolate, yes)


class DstPerformedDateTests(DataSafetyBase):
    def performed(self, row):
        record = ZonalLaboratory()
        apply_tblis_dst(record, row, lambda *args: None)
        return record.first_line_dst_performed_date, record.second_line_dst_performed_date

    def test_lj_set_up_date_first(self):
        row = {"ljdst1_date": "2025-06-20", "LJDST1_SETUPDATE": "2025-05-01", "mgitdst1_date": "2025-06-01"}
        self.assertEqual(self.performed(row)[0], date(2025, 5, 1))

    def test_then_mgit(self):
        self.assertEqual(self.performed({"mgitdst1_entrydate": "2025-05-03", "mgitdst1_date": "2025-06-01"})[0], date(2025, 5, 3))
        self.assertEqual(self.performed({"mgitdst1_date": "2025-06-01"})[0], date(2025, 6, 1))
        self.assertEqual(self.performed({"mgitdst2_date": "2025-07-01"})[1], date(2025, 7, 1))

    def test_nothing_without_a_dst_date(self):
        self.assertEqual(self.performed({}), (None, None))


class SmallFixTests(DataSafetyBase):
    def test_saving_a_zonal_form_updates_edcs_at_once(self):
        lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001")
        self.client.force_login(self.make_user("ctrl_save", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        response = self.client.post(reverse("nanopore:zonal-laboratory-update", args=[lab.pk]),
                                    {"screening": self.dar.pk, "unique_lab_no": "30009", "next": "/",
                                     "reason_for_change": "Lab number typed wrongly"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(EdcsTblisZonal.objects.get(screening=self.dar).unique_lab_no, "30009")

    def test_older_file_is_flagged(self):
        batch = TblisUploadBatch.objects.create(source_file_name="newer.csv")
        TblisRawData.objects.create(labno="1", upload_batch=batch, raw_data={"rctdate": "2026-09-30"})
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        csv.writer(handle).writerows([["labno", "spectype", "peripheralres_genexpert", "rctdate"], ["2", "Sputum", "MTB Detected", "2026-06-01"]])
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        result = process_raw_tblis_upload.apply(args=[handle.name, None, "older.csv"], kwargs={"dry_run": True}).get()
        self.assertEqual(result["older_than_latest"], {"file": "2026-06-01", "latest": "2026-09-30"})

    def test_edcs_export_is_for_export_roles(self):
        tech = self.make_user("lab_exp", [access.LABORATORY_TECHNICIAN], zones=[self.zone_a])
        self.client.force_login(tech)
        self.assertNotContains(self.client.get(reverse("nanopore:edcs-tblis-laboratory-list")), 'onclick="startCardExport')
        self.assertEqual(self.client.post(reverse("nanopore:edcs-tblis-export-trigger")).status_code, 403)
        self.client.force_login(self.make_user("ds_exp", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        self.assertContains(self.client.get(reverse("nanopore:edcs-tblis-laboratory-list")), 'onclick="startCardExport')

    def test_household_is_for_superusers(self):
        self.client.force_login(self.make_user("ds_house", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        for url in ("/household/list/", "/household/create/"):
            self.assertEqual(self.client.get(url).status_code, 403, url)
        self.assertEqual(self.client.post("/household/create/", {}).status_code, 403)


class DictionaryRuleTests(DataSafetyBase):
    """Data dictionary v0.2: 6a, 12a/12c/12f, 12h and question 11 entered by CTRL."""

    def overlay(self, row):
        EdcsTblisZonal.objects.filter(screening=self.dar).delete()
        record = EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001")
        from nanopore.tasks_tblis_raw import apply_tblis_transformations
        with mock.patch("nanopore.tasks_tblis_raw.mismatch_logger", return_value=lambda *args: None):
            apply_tblis_transformations(record, row, "30001")
        return record

    def test_no_dst_date_leaves_performed_empty(self):
        record = self.overlay({"rctdate": "2025-01-01"})
        self.assertEqual((record.phenotypic_performed_id, record.first_line_dst_performed_id, record.second_line_dst_performed_id),
                         (None, None, None))

    def test_another_zones_form_keeps_the_sites_answer(self):
        record = ZonalLaboratory(phenotypic_performed=self.no)
        apply_tblis_dst(record, {}, lambda *args: None, keep_unanswered=True)
        self.assertEqual(record.phenotypic_performed, self.no)

    def test_second_line_results_date_lj_first(self):
        record = ZonalLaboratory()
        apply_tblis_dst(record, {"ljdst2_date": "2025-07-02", "mgitdst2_date": "2025-07-01"}, lambda *args: None)
        self.assertEqual(record.second_line_dst_results_date, date(2025, 7, 2))

    def test_culture_performed_lj_then_mgit(self):
        self.assertEqual(self.overlay({"mgit_entrydate": "2025-02-01"}).culture_performed_id, 1)
        self.assertEqual(self.overlay({"lj_innocdate": "2025-02-01"}).culture_performed_id, 1)
        self.assertEqual(self.overlay({}).culture_performed_id, 2)

    def test_ctrl_answers_question_11(self):
        yes = YesNoNA.objects.create(pk=1, name="Yes", value=1)
        no = YesNoNA.objects.create(pk=2, name="No", value=2)
        lab = self.zonal_labs["B1"]
        self.client.force_login(self.make_user("ctrl_q11", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        url = reverse("nanopore:ctrl-isolate-update", args=[lab.pk])
        page = self.client.post(url, {"culture_isolate": yes.pk, "isolate_unique_lab_no": ""})
        self.assertIn("isolate_unique_lab_no", page.context["form"].errors)
        self.client.post(url, {"culture_isolate": yes.pk, "isolate_date": "2025-05-01", "isolate_unique_lab_no": "50001"})
        lab.refresh_from_db()
        self.assertEqual((lab.culture_isolate, lab.isolate_date, lab.isolate_unique_lab_no), (yes, date(2025, 5, 1), "50001"))
        self.client.post(url, {"culture_isolate": no.pk, "isolate_date": "2025-05-01", "isolate_unique_lab_no": "50001",
                               "reason_for_change": "Isolate was not sent after all"})
        lab.refresh_from_db()
        self.assertEqual((lab.culture_isolate, lab.isolate_date, lab.isolate_unique_lab_no), (no, None, None))


class DataDictionaryTests(DataSafetyBase):
    def workbook(self, folder):
        from openpyxl import Workbook
        from reports import data_dictionary as dd
        book = Workbook()
        sheet = book.active
        sheet.title = "EDCS"
        sheet.append(["form", "field_name", "field_name_tblis", "MAPPING EXPLANATIONS"])
        for name in dd.CORRECTIONS:
            sheet.append(["zonal_lab_ctrl", name + "  ", "old", "old text"])
        sheet.append(["zonal_lab_ctrl", "first_line_drugs", "", "Pending"])  # a second band row
        sheet.append(["screening", "culture_performed", "", "not this form"])
        path = os.path.join(folder, "source.xlsx")
        book.save(path)
        return path

    def test_issue_applies_the_corrections_and_change_log(self):
        from openpyxl import load_workbook
        from reports import data_dictionary as dd
        with tempfile.TemporaryDirectory() as folder, self.settings(DATA_DICTIONARY_DIR=folder):
            target, changed = dd.issue(self.workbook(folder))
            self.assertEqual(target.name, f"Tanzania_Data_Dictionary_v{dd.EDITED_VERSION}.xlsx")
            sheet = load_workbook(target)["EDCS"]
            rows = {(r[0], str(r[1]).strip(), i): r for i, r in enumerate(sheet.iter_rows(min_row=2, values_only=True))}
            texts = [r[3] for (form, name, _), r in rows.items() if name == "first_line_drugs"]
            self.assertEqual(texts, [dd.BANDS, dd.BANDS])
            self.assertTrue(all(r[3] == "not this form" for (form, _, _), r in rows.items() if form == "screening"))
            culture = next(r for (form, name, _), r in rows.items() if form == "zonal_lab_ctrl" and name == "culture_performed")
            self.assertEqual(culture[2], "lj_innocdate,mgit_entrydate")
            self.assertIn("Change log", load_workbook(target).sheetnames)

    def test_codebook_offers_the_newest_and_earlier_versions(self):
        from reports import data_dictionary as dd
        with tempfile.TemporaryDirectory() as folder, self.settings(DATA_DICTIONARY_DIR=folder):
            self.client.force_login(self.make_user("nurse_dict", [access.NURSE], sites=[self.a1]))
            self.assertContains(self.client.get(reverse("reports:codebook")), reverse("reports:data-dictionary", args=[dd.VERSION]))
            dd.keep_as_issued(self.workbook(folder), "0.1")
            dd.issue(self.workbook(folder))
            page = self.client.get(reverse("reports:codebook"))
            for version in (dd.VERSION, dd.EDITED_VERSION, "0.1"):
                self.assertContains(page, reverse("reports:data-dictionary", args=[version]))
            response = self.client.get(reverse("reports:data-dictionary", args=["0.1"]))
            self.assertEqual(response.status_code, 200)
            self.assertIn("Tanzania_Data_Dictionary_v0.1.xlsx", response["Content-Disposition"])
            b"".join(response.streaming_content)
            self.assertEqual(self.client.get(reverse("reports:data-dictionary", args=["9.9"])).status_code, 404)
            self.assertEqual(self.client.get("/reports/data-dictionary/v..%2F..%2Fsettings/").status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("reports:data-dictionary", args=["0.1"])).status_code, 302)

    def test_current_version_is_built_from_the_system(self):
        import io
        from openpyxl import load_workbook
        from reports import data_dictionary as dd
        from reports.dictionary_builder import DECISIONS
        with tempfile.TemporaryDirectory() as folder, self.settings(DATA_DICTIONARY_DIR=folder):
            self.client.force_login(self.make_user("nurse_dict3", [access.NURSE], sites=[self.a1]))
            response = self.client.get(reverse("reports:data-dictionary", args=[dd.VERSION]))
            self.assertIn(f"Tanzania_Data_Dictionary_v{dd.VERSION}.xlsx", response["Content-Disposition"])
            book = load_workbook(io.BytesIO(b"".join(response.streaming_content)))
        self.assertEqual(book.sheetnames, ["Summary", "Forms", "Data Dictionary", "Choices", "Mapping", "Decisions", "Change log"])
        rows = list(book["Data Dictionary"].iter_rows(min_row=2, values_only=True))
        variables = {(row[1], row[3]): row for row in rows}
        self.assertIn("TB-LIS (by isolate number)", variables[("Zonal Laboratory", "rifampicin")][9])
        self.assertIn("ljdst1_date", variables[("EDCS / TBLIS", "phenotypic_performed")][10])
        self.assertIn("CTRL (Nanopore form)", variables[("Zonal Laboratory", "nanopore_done")][9])
        self.assertEqual(len(list(book["Decisions"].iter_rows(min_row=3))), len(DECISIONS) + 1)
        self.assertTrue(any(row[0] == "YesNo" for row in book["Choices"].iter_rows(min_row=2, values_only=True)))


class DarLabNumberTests(DataSafetyBase):
    """Correcting a Dar es Salaam lab number shows the right TB-LIS results at once, not after the nightly sync."""

    def setUp(self):
        super().setUp()
        from options.models import MGITCultureResult
        self.positive = MGITCultureResult.objects.create(pk=1, name="Positive", value=1)
        self.negative = MGITCultureResult.objects.create(pk=2, name="Negative", value=2)
        YesNoNA.objects.create(pk=3, name="Na", value=98)
        accepted = {"spectype": "Sputum", "peripheralres_genexpert": "MTB Detected"}
        TblisRawData.objects.create(labno="30001", raw_data={**accepted, "labno": "30001", "mgit_res": "POSITIVE"})
        TblisRawData.objects.create(labno="30002", raw_data={**accepted, "labno": "30002", "mgit_res": "NEGATIVE"})
        self.lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        sync_with_latest_tblis(self.lab)
        self.assertEqual(self.edcs().mgit_results, self.positive)

    def edcs(self):
        return EdcsTblisZonal.objects.get(screening=self.dar)

    def correct(self, number):
        self.client.force_login(self.make_user(f"ctrl_{number}", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        response = self.client.post(reverse("nanopore:zonal-laboratory-update", args=[self.lab.pk]),
                                    {"screening": self.dar.pk, "unique_lab_no": number, "next": "/",
                                     "reason_for_change": "Lab number typed wrongly"})
        self.assertEqual(response.status_code, 302)

    def test_corrected_number_brings_its_own_results(self):
        self.correct("30002")
        record = self.edcs()
        self.assertEqual((record.unique_lab_no, record.mgit_results), ("30002", self.negative))

    def test_number_tblis_doesnt_have_drops_the_old_results(self):
        self.correct("30009")
        record = self.edcs()
        self.assertEqual((record.unique_lab_no, record.mgit_results), ("30009", None))

    def test_bulk_csv_upload_also_updates_at_once(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self._superuser())
        upload = SimpleUploadedFile("zonal.csv", f"PID,UniqueLabNo\n{self.dar.pid},30002\n".encode(), content_type="text/csv")
        self.client.post(reverse("nanopore:zonal-upload-csv"), {"file": upload})
        record = self.edcs()
        self.assertEqual((record.unique_lab_no, record.mgit_results), ("30002", self.negative))
        self.assertEqual(record.history.order_by("-history_date", "-history_id").first().history_source, "Zonal Lab CSV upload")

    def _superuser(self):
        from django.contrib.auth.models import User
        return User.objects.create_superuser("super_csv", "super@example.org", "x")



class ViewPagesTests(DataSafetyBase):
    """The Zonal Lab View button and the Dar EDCS/TBLIS view."""

    def test_zonal_view_is_the_whole_form_read_only(self):
        lab = self.zonal_labs["A1"]
        self.client.force_login(self.make_user("lab_view", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        url = reverse("nanopore:zonal-laboratory-detail", args=[lab.pk])
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertTrue(page.context["read_only"])
        self.assertTrue(all(field.disabled for field in page.context["form"].fields.values()))
        self.assertNotContains(page, "Save Zonal Laboratory")
        self.assertEqual(self.client.post(url, {"screening": lab.screening_id}).status_code, 405)

    def test_zonal_list_has_no_empty_columns(self):
        self.client.force_login(self.make_user("lab_list", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        page = self.client.get(reverse("nanopore:zonal-laboratory-list"))
        self.assertNotContains(page, "Test Name")
        self.assertNotContains(page, "Test Date")
        self.assertContains(page, "Lab No.")

    def test_dar_edcs_view_asks_dst_without_isolate(self):
        ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        sync_with_latest_tblis(ZonalLaboratory.objects.get(screening=self.dar))
        self.client.force_login(self.make_user("admin_view", [access.ADMIN]))
        dar = EdcsTblisZonal.objects.get(screening=self.dar)
        self.assertContains(self.client.get(reverse("nanopore:edcs-tblis-laboratory-view", args=[dar.pk])),
                            'data-dst-without-isolate="1"')
        other = EdcsTblisZonal.objects.create(screening=self.screenings["A1"])
        self.assertContains(self.client.get(reverse("nanopore:edcs-tblis-laboratory-view", args=[other.pk])),
                            'data-dst-without-isolate=""')



class EdcsButtonTests(DataSafetyBase):
    """View EDCS/TBLIS on the Zonal Lab and CTRL forms."""

    def edcs_url(self, record):
        return reverse("nanopore:edcs-tblis-laboratory-view", args=[record.pk])

    def test_zonal_form_links_to_its_record_or_says_not_built(self):
        lab = self.zonal_labs["A1"]
        self.client.force_login(self.make_user("lab_btn", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        form_url = reverse("nanopore:zonal-laboratory-update", args=[lab.pk])
        EdcsTblisZonal.objects.filter(screening=lab.screening).delete()
        self.assertContains(self.client.get(form_url), "EDCS/TBLIS record not built yet")
        record = EdcsTblisZonal.objects.create(screening=lab.screening)
        for url in (form_url, reverse("nanopore:zonal-laboratory-detail", args=[lab.pk])):
            self.assertContains(self.client.get(url), self.edcs_url(record))
        self.assertEqual(self.client.get(self.edcs_url(record)).status_code, 200)

    def test_new_form_has_no_button(self):
        self.client.force_login(self.make_user("lab_new", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        page = self.client.get(reverse("nanopore:zonal-laboratory-create") + f"?screening={self.screenings['A1'].pk}")
        self.assertNotContains(page, "View EDCS/TBLIS")
        self.assertNotContains(page, "not built yet")

    def test_ctrl_forms_link_to_every_zone(self):
        ctrl = self.make_user("ctrl_btn", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl])
        self.client.force_login(ctrl)
        other = self.zonal_labs["B1"]
        record = EdcsTblisZonal.objects.get_or_create(screening=other.screening)[0]
        self.assertContains(self.client.get(reverse("nanopore:ctrl-isolate-update", args=[other.pk])), self.edcs_url(record))
        self.assertEqual(self.client.get(self.edcs_url(record)).status_code, 200)
        dar_lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        sync_with_latest_tblis(dar_lab)
        dar = EdcsTblisZonal.objects.get(screening=self.dar)
        self.assertContains(self.client.get(reverse("nanopore:ctrl-dar-nanopore", args=[dar_lab.pk])), self.edcs_url(dar))

    def test_others_still_limited_to_their_sites(self):
        record = EdcsTblisZonal.objects.get_or_create(screening=self.zonal_labs["B1"].screening)[0]
        self.client.force_login(self.make_user("lab_a_only", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        self.assertEqual(self.client.get(self.edcs_url(record)).status_code, 404)
        self.client.force_login(self.make_user("nurse_btn", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(self.edcs_url(record)).status_code, 403)
