"""Raw TBLIS upload: reading any export format, date handling, filtering and preview."""
import datetime
import os
import tempfile

import openpyxl
from django.test import SimpleTestCase

from locations.models import Zone
from nanopore.models import EdcsTblisMismatch, EdcsTblisZonal, Screening, TblisRawData, TblisUploadBatch, ZonalLaboratory
from nanopore.models.discrepancies import TblisNotInEdcs
from nanopore.tasks_tblis_raw import process_raw_tblis_upload, sync_zonal_laboratory_daily
from nanopore.tblis_file import TblisFileError, filter_rows, read_tblis_file
from nanopore.test_access import AccessTestBase
from options.models import CultureMethod, YesNo

HEADER = ["labno", "spectype", "peripheralres_genexpert", "rctdate", "lj_innocdate", "mgitdst1_date", "volume"]
DETECTED = "MTB Detected - Rifampicin Sensitive"


def write_csv(rows, header=HEADER, bom=False):
    handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8-sig" if bom else "utf-8")
    handle.write(",".join(header) + "\n")
    for row in rows:
        handle.write(",".join(row) + "\n")
    handle.close()
    return handle.name


def write_xlsx(rows, header=HEADER, extra_sheet=True):
    workbook = openpyxl.Workbook()
    if extra_sheet:  # CTRL sometimes puts notes on other sheets
        workbook.active.title = "notes"
        workbook.active.append(["Lab No", "Raw Data"])
        sheet = workbook.create_sheet("data")
    else:
        sheet = workbook.active
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    path = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
    workbook.save(path)
    return path


class ReadTblisFileTests(SimpleTestCase):
    def tearDown(self):
        for path in getattr(self, "paths", []):
            os.unlink(path)

    def read(self, path):
        self.paths = getattr(self, "paths", []) + [path]
        return read_tblis_file(path)

    def test_csv_iso_dates(self):
        result = self.read(write_csv([["31151", "Sputum", DETECTED, "2025-04-23", "", "", "2"]]))
        self.assertEqual(result["date_order"], "iso")
        self.assertEqual(result["rows"][0]["rctdate"], "2025-04-23")

    def test_csv_day_first_dates(self):
        result = self.read(write_csv([
            ["1", "Sputum", DETECTED, "23/04/2025", "05/03/2025", "", ""],
        ]))
        self.assertEqual(result["date_order"], "dd/mm/yyyy")
        self.assertEqual(result["rows"][0]["rctdate"], "2025-04-23")
        self.assertEqual(result["rows"][0]["lj_innocdate"], "2025-03-05")

    def test_csv_month_first_dates(self):
        result = self.read(write_csv([
            ["1", "Sputum", DETECTED, "4/23/2026", "3/5/2026", "", ""],
        ]))
        self.assertEqual(result["date_order"], "mm/dd/yyyy")
        self.assertEqual(result["rows"][0]["lj_innocdate"], "2026-03-05")

    def test_csv_with_undecidable_dates_is_refused(self):
        with self.assertRaises(TblisFileError):
            self.read(write_csv([["1", "Sputum", DETECTED, "03/04/2025", "", "", ""]]))

    def test_csv_with_mixed_date_orders_is_refused(self):
        with self.assertRaises(TblisFileError):
            self.read(write_csv([
                ["1", "Sputum", DETECTED, "23/04/2025", "", "", ""],
                ["2", "Sputum", DETECTED, "4/23/2025", "", "", ""],
            ]))

    def test_unreadable_date_is_reported_not_silently_kept(self):
        result = self.read(write_csv([["31151", "Sputum", DETECTED, "2025-13-40", "", "", ""]]))
        self.assertEqual(result["rows"][0]["rctdate"], "")
        self.assertIn("labno 31151", result["problems"][0])
        self.assertIn("rctdate", result["problems"][0])

    def test_csv_with_bom_still_finds_labno(self):
        result = self.read(write_csv([["31151", "Sputum", DETECTED, "2025-04-23", "", "", ""]], bom=True))
        self.assertEqual(result["rows"][0]["labno"], "31151")

    def test_xlsx_uses_data_sheet_dates_and_text_lab_numbers(self):
        result = self.read(write_xlsx([
            [31151, "Sputum", DETECTED, datetime.datetime(2025, 4, 23, 0, 0), datetime.datetime(2025, 3, 5, 14, 30), None, 2.5],
            [31152.0, "Sputum", DETECTED, datetime.date(2025, 4, 24), None, None, 3],
        ]))
        self.assertEqual(result["sheet"], "data")
        self.assertEqual(result["rows"][0]["labno"], "31151")
        self.assertEqual(result["rows"][1]["labno"], "31152")
        self.assertEqual(result["rows"][0]["lj_innocdate"], "2025-03-05")  # time dropped
        self.assertEqual(result["rows"][0]["volume"], "2.5")

    def test_missing_required_columns_is_refused(self):
        with self.assertRaises(TblisFileError):
            self.read(write_csv([["1", "x"]], header=["labno", "spectype"]))

    def test_unsupported_extension_is_refused(self):
        path = tempfile.NamedTemporaryFile(suffix=".txt", delete=False).name
        with self.assertRaises(TblisFileError):
            self.read(path)


class FilterRowsTests(SimpleTestCase):
    def row(self, spectype, genexpert):
        return {"labno": "1", "spectype": spectype, "peripheralres_genexpert": genexpert}

    def test_filter_rules(self):
        rows = [
            self.row("Sputum", DETECTED),
            self.row("Sputum", "MTB Detected"),
            self.row("sputum", "MTB Trace Detected - Rifampicin Resistance Indeterminate"),
            self.row("Sputum", "MTB Not Detected"),
            self.row("Sputum", "Not Provided"),
            self.row("Sputum", ""),
            self.row("Isolate", DETECTED),
            self.row("Isolate", "Not Provided"),  # isolates often have no GeneXpert
            self.row("Not Provided", DETECTED),
        ]
        kept, left_out = filter_rows(rows)
        self.assertEqual(len(kept), 5)
        self.assertEqual(left_out, {"genexpert_not_detected": 1, "genexpert_missing": 2, "not_sputum": 1})


class UploadTaskTests(AccessTestBase):
    """Runs the upload task directly (no Celery worker) against small files."""

    def setUp(self):
        self.yes = YesNo.objects.get(name="Yes")
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        CultureMethod.objects.create(pk=1, value=1, name="Lj")
        CultureMethod.objects.create(pk=2, value=2, name="Mgit")
        # A Dar es Salaam (CTRL) participant whose Zonal Lab only has the lab number.
        self.zonal = self.zonal_labs["A1"]
        self.screening = self.zonal.screening
        self.screening.pid = "DF_TZ_SS2_18_001"
        Screening = type(self.screening)
        Screening.objects.filter(pk=self.screening.pk).update(pid="DF_TZ_SS2_18_001")
        self.zonal.refresh_from_db()
        self.path = write_csv([
            [self.zonal.unique_lab_no, "Sputum", DETECTED, "2025-04-23", "2025-04-25", "2025-06-01", "2"],
            ["99999", "Sputum", "MTB Not Detected", "2025-04-23", "", "", "1"],
            ["99998", "Isolate", DETECTED, "2025-04-23", "", "", "1"],
        ])

    def tearDown(self):
        os.unlink(self.path)

    def run_upload(self, dry_run):
        return process_raw_tblis_upload.apply(args=[self.path, None, "test.csv"], kwargs={"dry_run": dry_run}).get()

    def test_preview_saves_nothing(self):
        result = self.run_upload(dry_run=True)
        self.assertTrue(result["preview"])
        self.assertEqual(result["rows_in_file"], 3)
        self.assertEqual(result["rows_kept"], 2)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["isolates_unmatched"], 1)
        self.assertEqual(TblisUploadBatch.objects.count(), 0)
        self.assertEqual(TblisRawData.objects.count(), 0)
        self.assertFalse(EdcsTblisZonal.objects.filter(screening=self.screening).exists())

    def test_upload_keeps_only_filtered_rows_and_merges(self):
        result = self.run_upload(dry_run=False)
        self.assertEqual(result["rows_left_out"], 1)
        self.assertEqual(result["left_out_by_reason"], {"GeneXpert: MTB Not Detected": 1})
        self.assertEqual(set(TblisRawData.objects.values_list("labno", flat=True)), {self.zonal.unique_lab_no, "99998"})
        edcs = EdcsTblisZonal.objects.get(screening=self.screening)
        self.assertEqual(str(edcs.date_sputum_received), "2025-04-23")
        self.assertEqual(edcs.culture_performed_id, 1)
        # MGIT first-line DST result date alone now counts as "performed"
        self.assertEqual(edcs.first_line_dst_performed_id, 1)

    def test_same_volume_written_differently_is_not_a_mismatch(self):
        self.run_upload(dry_run=False)
        self.run_upload(dry_run=False)  # EDCS now holds 2.0, the file says "2"
        self.assertFalse(EdcsTblisMismatch.objects.filter(field_name="sample_volume").exists())

    def test_unusable_file_reports_why(self):
        bad = write_csv([["1", "Sputum", DETECTED, "03/04/2025", "", "", ""]])
        try:
            result = process_raw_tblis_upload.apply(args=[bad, None, "bad.csv"]).get()
        finally:
            os.unlink(bad)
        self.assertIn("day/month", result["file_error"])


class IsolateMergeTests(AccessTestBase):
    """Other zones' isolates: TB-LIS gives the DST by the number CTRL entered; nothing else changes."""
    HEADER = ["labno", "spectype", "peripheralres_genexpert", "rctdate", "ljdst1_date", "ljdst1_rifampicin", "LJDST1_SETUPDATE", "lj_res"]

    def setUp(self):
        YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.yes = YesNo.objects.get(pk=1)
        self.lab = self.zonal_labs["B1"]
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(
            isolate_unique_lab_no="50001", date_sputum_received=datetime.date(2025, 1, 5), sample_volume=5,
        )
        self.paths = []
        self.addCleanup(lambda: [os.unlink(path) for path in self.paths])

    def upload(self, *rows):
        path = write_csv(list(rows), header=self.HEADER)
        self.paths.append(path)
        return process_raw_tblis_upload.apply(args=[path, None, "test.csv"]).get()

    def isolate_row(self, labno="50001", dst_date="2025-06-01"):
        return [labno, "Isolate", "Not Provided", "2025-05-01", dst_date, "", "2025-05-02" if dst_date else "", "Positive"]

    def test_isolate_row_fills_only_the_dst_section(self):
        result = self.upload(self.isolate_row())
        self.assertEqual((result["isolates_merged"], result["isolates_unmatched"], result["updated"]), (1, 0, 0))
        lab = ZonalLaboratory.objects.get(pk=self.lab.pk)
        self.assertEqual(lab.phenotypic_performed_id, 1)
        self.assertEqual(lab.first_line_dst_performed_id, 1)
        self.assertEqual(str(lab.first_line_dst_results_date), "2025-06-01")
        # The site's sections stay as they were, and the sync carries the DST to EDCS/TBLIS
        self.assertEqual(str(lab.date_sputum_received), "2025-01-05")
        self.assertEqual(lab.sample_volume, 5)
        self.assertIsNone(lab.lj_results_id)
        edcs = EdcsTblisZonal.objects.get(screening=lab.screening)
        self.assertEqual(edcs.first_line_dst_performed_id, 1)

    def test_row_without_dst_does_not_undo_a_yes(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(first_line_dst_performed=self.yes)
        self.upload(self.isolate_row(dst_date=""))
        lab = ZonalLaboratory.objects.get(pk=self.lab.pk)
        self.assertEqual(lab.first_line_dst_performed_id, 1)
        self.assertEqual(lab.second_line_dst_performed_id, 2)

    def test_unmatched_isolate_is_reported(self):
        result = self.upload(self.isolate_row(labno="50002"))
        self.assertEqual((result["isolates_merged"], result["isolates_unmatched"]), (0, 1))
        self.assertTrue(TblisNotInEdcs.objects.filter(labno="50002").exists())
        self.assertIsNone(ZonalLaboratory.objects.get(pk=self.lab.pk).first_line_dst_performed_id)

    def test_isolate_row_never_merges_by_unique_lab_number(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(isolate_unique_lab_no=None, unique_lab_no="50001")
        self.upload(self.isolate_row())
        self.assertIsNone(ZonalLaboratory.objects.get(pk=self.lab.pk).first_line_dst_performed_id)

    def test_dar_records_ignore_isolate_rows(self):
        Screening.objects.filter(pk=self.lab.screening_id).update(pid="DF_TZ_SS2_18_009")
        Zone.objects.filter(pk=self.zone_b.pk).update(name="Dar es salaam")
        self.upload(self.isolate_row())
        self.assertIsNone(ZonalLaboratory.objects.get(pk=self.lab.pk).first_line_dst_performed_id)

    def test_number_entered_after_the_upload_merges_at_once_and_daily(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(isolate_unique_lab_no=None)
        self.upload(self.isolate_row())
        lab = ZonalLaboratory.objects.get(pk=self.lab.pk)
        self.assertIsNone(lab.first_line_dst_performed_id)
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(isolate_unique_lab_no="50001")
        sync_zonal_laboratory_daily.apply().get()
        self.assertEqual(ZonalLaboratory.objects.get(pk=self.lab.pk).first_line_dst_performed_id, 1)
        self.assertEqual(EdcsTblisZonal.objects.get(screening=lab.screening).first_line_dst_performed_id, 1)
