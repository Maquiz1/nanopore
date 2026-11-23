"""
The study's data dictionary (the study team's Excel workbook), as issued versions.

Each version is a file Tanzania_Data_Dictionary_v<version>.xlsx in DATA_DICTIONARY_DIR
(the data_dictionary/ folder next to backend/, kept out of git). The Codebook page offers
the newest for download, and earlier ones as issued.

From v0.3 the current version is built from the system when it is downloaded
(reports/dictionary_builder.py), so it needs no copying. Issued earlier versions (v0.1 as
received, v0.2 corrected by issue() below) are files copied with copy-dictionary-to-server.sh.
"""
import re
import shutil
from pathlib import Path

from django.conf import settings

VERSION = "0.3"  # built from the system when downloaded (reports/dictionary_builder.py)
VERSION_DATE = "2026-11-23"
EDITED_VERSION = "0.2"  # the last version made by correcting the study team's workbook (issue())
PREFIX = "Tanzania_Data_Dictionary_v"
SHEET = "EDCS"
FORM = "zonal_lab_ctrl"
EXPLANATION, SOURCES = "MAPPING EXPLANATIONS", "field_name_tblis"

CHANGE_LOG = [
    ("0.1", "2026-11-23", "Tanzania_data_dictionary_version_2026_11_23_EWT.xlsx as received, with the MAPPING EXPLANATIONS column."),
    ("0.2", "2026-11-23", "Mapping explanations matched to the system: 4 volume, 6a/6b culture (LJ then MGIT), 10 LJ and MGIT "
     "results, 11 isolate (Dar es Salaam Na; other zones by the zone's staff or CTRL), 12a/12c/12f empty when TB-LIS has no "
     "DST date, 12d/12g LJ set-up date then MGIT, 12h LJ then MGIT, 15e copy error, LPA from TB-LIS except the band "
     "checkboxes, Nanopore entered by CTRL (Dar es Salaam) or the zone's staff."),
]

DAR, OTHERS = "Dar es Salaam", "Other zones"
NANOPORE = (f"Not from TB-LIS. {DAR}: entered by CTRL on its Nanopore form. {OTHERS}: entered by the zone's staff "
            "on the Zonal Lab form.")
BANDS = (f"Not from TB-LIS (TB-LIS has no bands). {DAR}: ticked by CTRL on its LPA form, for the lines TB-LIS says "
         f"were done. {OTHERS}: ticked by the zone's staff on the Zonal Lab form.")

# field_name -> {column: new text}, for every row of that field in the zonal_lab_ctrl form
CORRECTIONS = {
    "sample_volume": {EXPLANATION: "If volume is available, use it (mL), else empty."},
    "culture_performed": {SOURCES: "lj_innocdate,mgit_entrydate",
                          EXPLANATION: "If lj_innocdate is available culture_performed = Yes; if it is missing, check "
                                       "mgit_entrydate: if available Yes; else No."},
    "culture_method": {EXPLANATION: "Checkbox: LJ (1) when lj_innocdate is available, MGIT (2) when mgit_entrydate is "
                                    "available, both when both, else empty."},
    "lj_results": {EXPLANATION: "lj_results from lj_res (see TBLIS_EDCS_OPTIONS_MAPPING); any other positive result without "
                                "'+' is Scanty; unknown text is left empty and listed for checking. If id_res = 'Mycobacteria "
                                "other than M.tuberculosis' and an LJ culture was done, lj_results = MOTT (7). Else empty."},
    "mgit_results": {EXPLANATION: "mgit_results from mgit_res: any 'colon...' result is Positive, negative stays Negative, "
                                  "contaminated is Contamination, POSITIVE FOR NTM is MOTT. 'No colonies', 'Nil', '0' and "
                                  "unknown text are left empty and listed for checking. If id_res = 'Mycobacteria other "
                                  "than M.tuberculosis' and an MGIT culture was done, MOTT (4). Else empty."},
    "culture_isolate": {EXPLANATION: f"{DAR}: Na (98), as CTRL cultures every sample and TB-LIS merges by lab number. "
                                     f"{OTHERS}: not from TB-LIS; entered on the Zonal Lab form by the zone's staff, or "
                                     "by CTRL; Yes or No, else empty."},
    "isolate_date": {EXPLANATION: f"{DAR}: empty. {OTHERS}: not from TB-LIS; entered by the zone's staff or by CTRL."},
    "isolate_unique_lab_no": {EXPLANATION: f"{DAR}: empty. {OTHERS}: entered by CTRL. TB-LIS Isolate rows are matched by "
                                           "this number and give the DST (12-14). DST is asked for other zones only "
                                           f"when 11 = Yes; for {DAR} it is asked for every positive culture."},
    "first_line_dst_performed_date": {SOURCES: "LJDST1_SETUPDATE,mgitdst1_entrydate,mgitdst1_date",
                                      EXPLANATION: "If LJDST1_SETUPDATE is available use it; if missing, mgitdst1_entrydate; "
                                                   "if missing, mgitdst1_date (TB-LIS has no MGIT set-up date); else empty."},
    "second_line_dst_performed_date": {SOURCES: "LJDST2_SETUPDATE,mgitdst2_entrydate,mgitdst2_date",
                                       EXPLANATION: "If LJDST2_SETUPDATE is available use it; if missing, "
                                                    "mgitdst2_entrydate; if missing, mgitdst2_date; else empty."},
    "xpert_xdr_capreomycin": {EXPLANATION: "Variable in EDCS: xpert_xdr_capreomycin."},
    "first_line_lpa": {EXPLANATION: "From TB-LIS: Yes if lpa1_date or lpa1_mtbc is available, else No."},
    "first_line_lpa_date": {EXPLANATION: "From TB-LIS: lpa1_date if available, else empty."},
    "second_line_lpa": {EXPLANATION: "From TB-LIS: Yes if lpa2_date or lpa2_mtbc is available, else No."},
    "second_line_lpa_date": {EXPLANATION: "From TB-LIS: lpa2_date if available, else empty."},
    "first_line_drugs": {EXPLANATION: BANDS},
    "second_line_drugs": {EXPLANATION: BANDS},
    **{name: {EXPLANATION: NANOPORE} for name in (
        "nanopore_sequencing_date", "epi_to_me_date", "nanopore_results", "sequencing_delayed", "sequencing_delayed_days",
        "sequencing_delayed_reasons", "sequencing_delayed_others")},
}


def folder():
    return Path(settings.DATA_DICTIONARY_DIR)


def filename(version=VERSION):
    return f"{PREFIX}{version}.xlsx"


def versions():
    """[(version, path)] newest first: the current version (path None: built when downloaded) and the issued files."""
    found = [((tuple(int(part) for part in VERSION.split(".")), VERSION, None))]
    for path in folder().glob(f"{PREFIX}*.xlsx"):
        version = path.stem[len(PREFIX):]
        if version != VERSION and re.fullmatch(r"\d+(\.\d+)*", version):
            found.append((tuple(int(part) for part in version.split(".")), version, path))
    return [(version, path) for _, version, path in sorted(found, reverse=True)]


def keep_as_issued(source, version):
    """Store a workbook exactly as received, as an issued version."""
    folder().mkdir(parents=True, exist_ok=True)
    target = folder() / filename(version)
    shutil.copyfile(source, target)
    return target


def issue(source):
    """Write EDITED_VERSION: the source workbook with CORRECTIONS applied and the change log. Returns (path, cells changed)."""
    from openpyxl import load_workbook

    book = load_workbook(source)
    sheet = book[SHEET]
    header = {str(cell.value).strip(): cell.column for cell in sheet[1] if cell.value}
    missing = {SOURCES, EXPLANATION, "field_name", "form"} - set(header)
    if missing:
        raise ValueError(f"The {SHEET} sheet has no column {', '.join(sorted(missing))}.")

    changed, seen = 0, set()
    for row in sheet.iter_rows(min_row=2):
        form = str(row[header["form"] - 1].value or "").strip()
        name = str(row[header["field_name"] - 1].value or "").strip()
        if not form.startswith(FORM) or name not in CORRECTIONS:
            continue
        seen.add(name)
        for column, text in CORRECTIONS[name].items():
            cell = row[header[column] - 1]
            if cell.value != text:
                cell.value = text
                changed += 1
    if set(CORRECTIONS) - seen:
        raise ValueError(f"Not in the {SHEET} sheet: {', '.join(sorted(set(CORRECTIONS) - seen))}.")

    if "Change log" in book.sheetnames:
        del book["Change log"]
    log = book.create_sheet("Change log")
    log.append(["Version", "Date", "Changes"])
    for line in CHANGE_LOG:
        log.append(list(line))
    log.column_dimensions["C"].width = 120

    folder().mkdir(parents=True, exist_ok=True)
    target = folder() / filename(EDITED_VERSION)
    book.save(target)
    return target, changed


def write_current():
    """Save the current version as a file, e.g. to keep it as issued before the next version."""
    from reports.dictionary_builder import build_workbook
    folder().mkdir(parents=True, exist_ok=True)
    target = folder() / filename()
    build_workbook().save(target)
    return target
