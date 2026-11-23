"""TB-LIS rows stored before dates were read (nanopore/tblis_file.normalize_stored_dates)."""
from django.test import TestCase

from nanopore.models import TblisRawData, TblisUploadBatch
from nanopore.tblis_file import normalize_stored_dates


class StoredDateTests(TestCase):
    def rows(self, name, *dates):
        batch = TblisUploadBatch.objects.create(source_file_name=name)
        return [TblisRawData.objects.create(labno=f"{name}-{i}", upload_batch=batch, raw_data={"rctdate": d, "lj_date": d, "spectype": "Sputum"})
                for i, d in enumerate(dates)]

    def stored(self, row):
        return TblisRawData.objects.get(pk=row.pk).raw_data

    def test_month_first_upload_is_rewritten(self):
        a, b = self.rows("mdy", "3/24/2025", "4/5/2025")
        result = normalize_stored_dates(TblisRawData)
        self.assertEqual((self.stored(a)["rctdate"], self.stored(b)["lj_date"]), ("2025-03-24", "2025-04-05"))
        self.assertEqual((self.stored(a)["_dates_read_as"], self.stored(a)["spectype"]), ("mm/dd/yyyy", "Sputum"))
        self.assertEqual((result["rows"], result["dates"]), (2, 4))

    def test_day_first_upload_is_rewritten(self):
        (row,) = self.rows("dmy", "24/03/2025")
        normalize_stored_dates(TblisRawData)
        self.assertEqual(self.stored(row)["rctdate"], "2025-03-24")

    def test_undecidable_or_mixed_uploads_are_left_alone(self):
        (ambiguous,) = self.rows("ambiguous", "3/4/2025")
        mixed = self.rows("mixed", "24/03/2025", "3/24/2025")
        result = normalize_stored_dates(TblisRawData)
        self.assertEqual(self.stored(ambiguous)["rctdate"], "3/4/2025")
        self.assertEqual(self.stored(mixed[1])["rctdate"], "3/24/2025")
        self.assertEqual(len(result["skipped"]), 2)

    def test_iso_rows_and_a_second_run_change_nothing(self):
        (iso,) = self.rows("iso", "2025-03-24")
        self.rows("mdy", "3/24/2025")
        normalize_stored_dates(TblisRawData)
        again = normalize_stored_dates(TblisRawData)
        self.assertEqual((again["rows"], self.stored(iso)), (0, {"rctdate": "2025-03-24", "lj_date": "2025-03-24", "spectype": "Sputum"}))

    def test_each_upload_is_read_in_its_own_order(self):
        (us,) = self.rows("mdy", "3/24/2025")
        (uk,) = self.rows("dmy", "24/03/2025")
        (short,) = self.rows("mdy-short", "3/4/2025", "12/25/2025")[:1]
        normalize_stored_dates(TblisRawData)
        self.assertEqual((self.stored(us)["rctdate"], self.stored(uk)["rctdate"], self.stored(short)["rctdate"]),
                         ("2025-03-24", "2025-03-24", "2025-03-04"))
