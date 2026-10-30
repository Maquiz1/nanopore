"""
Reading and preparing a raw TBLIS export before it is merged.

TBLIS exports arrive as .xlsx, .xls or .csv, and the CSV exports have used three
different date formats over time (yyyy-mm-dd, dd/mm/yyyy and mm/dd/yyyy). This
module turns any of them into the same thing: a list of rows whose values are
plain text, with every date written as yyyy-mm-dd. Nothing is guessed silently:
dates that cannot be read are reported, and a CSV whose day/month order cannot
be worked out is refused.

Then only the rows the study uses are kept (filter_rows):
  * Dar es Salaam samples: spectype is Sputum, and peripheralres_genexpert is
    "MTB Detected ..." or "MTB Trace Detected ...".
  * Other zones' isolates sent to CTRL: spectype is Isolate. They give the DST
    only (tasks_tblis_raw.merge_isolate_dst) and often have no GeneXpert.
Everything else ("MTB Not Detected", "Not Provided", blank, other specimens) is
left out of the merge.
"""
import csv
import datetime
import io
import os
import re
from collections import Counter

# Every TBLIS date column (the merge reads most of them).
DATE_COLUMNS = {
    "rctdate", "colldate", "fm_date", "fm_entrydate", "zn_date", "lj_date", "lj_innocdate",
    "lj_entrydate", "mgit_date", "mgit_contdate", "mgit_entrydate", "id_date", "gxxdr_date",
    "lpa1_date", "lpa1_entrydate", "lpa2_date", "lpa2_entrydate", "ljdst1_date", "LJDST1_SETUPDATE",
    "LJDST1_DFCDATE", "ljdst1_entrydate", "LJDST2_SETUPDATE", "LJDST2_DFCDATE", "ljdst2_entrydate",
    "mgitdst1_date", "mgitdst2_date", "mgitdst1_entrydate", "mgitdst2_entrydate",
}
REQUIRED_COLUMNS = ("labno", "spectype", "peripheralres_genexpert")
MAX_REPORTED_PROBLEMS = 200

ISO_DATE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T].*)?$")
SLASH_DATE = re.compile(r"^(\d{1,2})[/.](\d{1,2})[/.](\d{4})(?:\s.*)?$")

FILTER_REASONS = {
    "not_sputum": "Specimen is not Sputum or Isolate",
    "genexpert_not_detected": "GeneXpert: MTB Not Detected",
    "genexpert_missing": "GeneXpert: Not Provided / blank",
    "genexpert_other": "GeneXpert: other result",
}


class TblisFileError(Exception):
    """The file cannot be used at all (wrong format, missing columns, unknown date order)."""


# ── reading ────────────────────────────────────────────────────────────────

def _cell_to_text(value):
    if value is None:
        return ""
    if isinstance(value, datetime.datetime):
        if value.time() == datetime.time(0, 0):
            return value.strftime("%Y-%m-%d")
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))  # 31151.0 -> "31151" (lab numbers, counts)
    return str(value).strip()


def _pick_sheet(sheets):
    """The data sheet is the one with the TBLIS columns; exports can carry extra note sheets."""
    for name, rows in sheets:
        header = [_cell_to_text(h) for h in (rows[0] if rows else [])]
        if all(col in header for col in ("labno", "spectype")):
            return name, header, rows[1:]
    raise TblisFileError("No sheet in this workbook has the TBLIS columns 'labno' and 'spectype'.")


def _read_xlsx(path):
    import openpyxl
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheets = [(ws.title, list(ws.iter_rows(values_only=True))) for ws in workbook.worksheets]
    return _pick_sheet(sheets)


def _read_xls(path):
    try:
        import xlrd
    except ImportError as exc:
        raise TblisFileError("Reading .xls files needs the 'xlrd' package (pip install xlrd).") from exc
    book = xlrd.open_workbook(path)
    sheets = []
    for sheet in book.sheets():
        rows = []
        for r in range(sheet.nrows):
            row = []
            for c in range(sheet.ncols):
                cell = sheet.cell(r, c)
                if cell.ctype == xlrd.XL_CELL_DATE:
                    row.append(xlrd.xldate.xldate_as_datetime(cell.value, book.datemode))
                else:
                    row.append(cell.value)
            rows.append(row)
        sheets.append((sheet.name, rows))
    return _pick_sheet(sheets)


def _read_csv(path):
    data = open(path, "rb").read()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252")
    first_line = text.split("\n", 1)[0]
    delimiter = max([",", ";", "\t"], key=first_line.count)
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if not rows:
        raise TblisFileError("The file is empty.")
    return "csv", rows[0], rows[1:]


def read_tblis_file(path):
    """
    Read a TBLIS export. Returns a dict:
      rows        list of {column: text}, dates as yyyy-mm-dd
      columns     column names
      sheet       sheet used ("csv" for CSV files)
      date_order  how text dates were read ("iso", "dd/mm/yyyy", "mm/dd/yyyy", "excel")
      problems    ["Row 12 (labno 31151): lj_date '31/13/2025' is not a valid date", ...]
    Raises TblisFileError when the file can't be used.
    """
    ext = os.path.splitext(path)[1].lower()
    readers = {".xlsx": _read_xlsx, ".xlsm": _read_xlsx, ".xls": _read_xls, ".csv": _read_csv}
    if ext not in readers:
        raise TblisFileError(f"Unsupported file type '{ext}'. Upload a .xlsx, .xls or .csv file.")
    sheet, header, raw_rows = readers[ext](path)

    columns = [_cell_to_text(h) for h in header]
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise TblisFileError(f"The file is missing required column(s): {', '.join(missing)}.")

    rows = []
    for raw in raw_rows:
        values = [_cell_to_text(v) for v in raw]
        if not any(values):
            continue
        rows.append({col: (values[i] if i < len(values) else "") for i, col in enumerate(columns) if col})

    date_order = detect_date_order(rows)
    problems = normalize_dates(rows, date_order)
    return {
        "rows": rows,
        "columns": [c for c in columns if c],
        "sheet": sheet,
        "date_order": date_order,
        "problems": problems,
    }


# ── dates ──────────────────────────────────────────────────────────────────

def detect_date_order(rows):
    """
    Work out how slash dates (03/04/2025) are written in this file.
    A first part above 12 means dd/mm, a second part above 12 means mm/dd.
    """
    first_over_12 = second_over_12 = slash_dates = 0
    for row in rows:
        for col in DATE_COLUMNS:
            match = SLASH_DATE.match(row.get(col, ""))
            if not match:
                continue
            slash_dates += 1
            first_over_12 += int(match.group(1)) > 12
            second_over_12 += int(match.group(2)) > 12
    if not slash_dates:
        return "iso"
    if first_over_12 and second_over_12:
        raise TblisFileError(
            "Dates in this file are written both as day/month and month/day, so they can't be read safely. "
            "Ask CTRL for the export as .xlsx, or fix the date columns."
        )
    if first_over_12:
        return "dd/mm/yyyy"
    if second_over_12:
        return "mm/dd/yyyy"
    raise TblisFileError(
        "Dates are written like 03/04/2025 and every day and month is 12 or below, so it's impossible to tell "
        "day/month from month/day. Ask CTRL for the export as .xlsx."
    )


def _to_iso(value, date_order):
    match = ISO_DATE.match(value)
    if match:
        year, month, day = (int(g) for g in match.groups())
    else:
        match = SLASH_DATE.match(value)
        if not match:
            return None
        a, b, year = (int(g) for g in match.groups())
        day, month = (a, b) if date_order == "dd/mm/yyyy" else (b, a)
    try:
        return datetime.date(year, month, day).isoformat()
    except ValueError:
        return None


def normalize_dates(rows, date_order):
    """Rewrite every date column as yyyy-mm-dd. Unreadable dates are reported and cleared."""
    problems = []
    for index, row in enumerate(rows, start=2):  # row 1 is the header
        for col in DATE_COLUMNS:
            value = row.get(col, "")
            if not value:
                continue
            iso = _to_iso(value, date_order)
            if iso is None:
                problems.append(f"Row {index} (labno {row.get('labno', '?')}): {col} '{value}' is not a valid date")
                row[col] = ""
            else:
                row[col] = iso
    return problems


# ── filtering ──────────────────────────────────────────────────────────────

def is_isolate(row):
    return row.get("spectype", "").strip().lower() == "isolate"


def filter_reason(row):
    """None when the row is used for the merge, otherwise the reason it's left out."""
    if is_isolate(row):
        return None
    if row.get("spectype", "").strip().lower() != "sputum":
        return "not_sputum"
    genexpert = row.get("peripheralres_genexpert", "").strip().lower()
    if genexpert.startswith(("mtb detected", "mtb trace detected")):
        return None
    if not genexpert or genexpert == "not provided":
        return "genexpert_missing"
    if genexpert.startswith("mtb not detected"):
        return "genexpert_not_detected"
    return "genexpert_other"


def filter_rows(rows):
    """Split rows into the ones used for the merge and counts of the ones left out, by reason."""
    kept, left_out = [], Counter()
    for row in rows:
        reason = filter_reason(row)
        if reason:
            left_out[reason] += 1
        else:
            kept.append(row)
    return kept, dict(left_out)
