"""
Data dictionary v0.3 onwards, built from the system itself (like ~/projects/dimension's layout):
Summary, Forms, Data Dictionary, Choices, Mapping (Zonal Lab and TB-LIS), Decisions, Change log.

It is built when downloaded, so it always matches the forms, options and merge rules in use.
reports/data_dictionary.py lists it with the issued earlier versions.
"""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

TITLE = "DREAM Fund Nanopore TB Sequencing (Tanzania): Data Dictionary"
NAVY = "1F3864"
HEADER_FILL, HEADER_FONT = PatternFill("solid", fgColor=NAVY), Font(bold=True, color="FFFFFF")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")

DAR, OTHERS = "Dar es Salaam", "Other zones"

# key -> (form, completed by, where and when)
FORMS = {
    "screening": ("Screening", "Nurse or clinician at the clinic", "Every presumptive TB patient screened"),
    "enrollment": ("Enrollment", "Nurse or clinician", "Eligible participants who consent"),
    "clinic_lab": ("Clinic Laboratory", "Clinic laboratory", "Each enrolled participant's sputum at the clinic"),
    "zonal_lab": ("Zonal Laboratory", f"{DAR}: CTRL (lab number, remarks, Nanopore, LPA bands). {OTHERS}: the zone's laboratory; CTRL adds the isolate number",
                  "Sputum sent to the zonal laboratory (Substudy 2)"),
    "edcs_tblis": ("EDCS / TBLIS", "Nobody: rebuilt by the system from the Zonal Lab form and TB-LIS",
                   f"{DAR}: TB-LIS results by lab number. {OTHERS}: copy of the Zonal Lab form with the DST from TB-LIS"),
    "diagnosis": ("Diagnosis", "Clinician", "Diagnosis, treatment and outcome"),
    "regimen": ("Regimen Changes", "Clinician (from the Diagnosis form)", "Each change of TB regimen"),
}

# What each Zonal Lab / EDCS variable is filled by
ZONAL_SOURCE_RULES = (
    (("unique_lab_no", "remarks"), f"{DAR}: CTRL. {OTHERS}: the zone's laboratory."),
    (("culture_isolate", "isolate_date"), f"{DAR}: Na / empty. {OTHERS}: the zone's laboratory or CTRL."),
    (("isolate_unique_lab_no",), f"{DAR}: empty. {OTHERS}: CTRL."),
    (("first_line_drugs", "second_line_drugs"), f"{DAR}: CTRL (LPA form). {OTHERS}: the zone's laboratory."),
)

DECISIONS = [
    # (ID, date, area, question, decision)
    ("D01", "2026-10", "Merge", "Which TB-LIS rows are merged?", "Dar es Salaam: Sputum with GeneXpert 'MTB Detected' or 'MTB Trace Detected', matched by unique lab number. Other zones: Isolate rows only, matched by the isolate number CTRL enters, giving the phenotypic DST only."),
    ("D02", "2026-10", "Who enters", "Who enters Dar es Salaam data that TB-LIS doesn't have?", "CTRL: the lab number and remarks on the Zonal Lab form, Nanopore on its Nanopore form, the LPA bands on its LPA form."),
    ("D03", "2026-10", "Who enters", "Who enters other zones' data?", "The zone's laboratory on the Zonal Lab form, including Nanopore and LPA bands. CTRL enters the isolate number and may answer question 11."),
    ("D04", "2026-10", "Queries", "Is EDCS/TBLIS edited?", "No: it is read only and rebuilt daily. Fixes are made on the Zonal Lab form, or in TB-LIS followed by a new upload."),
    ("D05", "2026-11", "Queries", "A Dar es Salaam positive culture without DST?", "Not a query: not every positive culture gets DST, and the DST comes from TB-LIS. Listed for information on the Positive culture, no DST page (above TB-LIS follow-up), where the study team decides whether to ask CTRL for DST, until an upload brings it (changed from 'stays a query', 25 Nov 2026)."),
    ("D06", "2026-11", "Queries", "Isolate sent to CTRL with DST not done (other zones)?", "Not a query: listed for information on the Positive culture, no DST page and under CTRL isolates > Waiting for DST once CTRL has entered the isolate number, until TB-LIS has the DST (changed from 'stays a query', 25 Nov 2026)."),
    ("D07", "2026-11", "Queries", "Nanopore answered No?", "Fine; only a blank answer is a query, and nothing behind No is asked. Hidden answers are cleared on save."),
    ("D08", "2026-11", "Data dictionary", "Question 11 for Dar es Salaam?", "Na, with no isolate date or number; DST is asked whatever the isolate answer. Other zones: DST only when 11 = Yes."),
    ("D09", "2026-11", "Data dictionary", "12a / 12c / 12f when TB-LIS has no DST date?", "Empty (not No). On another zone's form the site's own answer stays. After 12a = No no further DST question is asked."),
    ("D10", "2026-11", "Data dictionary", "12d / 12g date of performing DST?", "LJ set-up date; if missing the MGIT DST entry date, then the MGIT DST result date (TB-LIS has no MGIT set-up date)."),
    ("D11", "2026-11", "Data dictionary", "12e / 12h DST results date?", "LJ result date first, then MGIT."),
    ("D12", "2026-11", "Data dictionary", "6a culture performed?", "Yes when there is an LJ inoculation date; if missing, an MGIT entry date; otherwise No."),
    ("D13", "2026-11", "Data dictionary", "LPA (16-19)?", "Merged from TB-LIS (done, date, MTB, RIF, INH) except the band checkboxes, which CTRL or the zone's staff tick."),
    ("D14", "2026-11", "Merge", "What does a new TB-LIS file change?", "In the file and accepted: used. In the file and rejected: the TB-LIS values go (the form's own stay) and the record is listed for CTRL. Not in the file: the last accepted result stays, marked 'Not in latest file'. Exports do not always hold every earlier lab number."),
    ("D15", "2026-11", "Merge", "A blank in TB-LIS for another zone's isolate DST?", "Takes back what TB-LIS gave; what the site entered stays."),
    ("D16", "2026-11", "Merge", "MGIT text 'No colonies', 'Nil' or unknown?", "Left empty and listed with the mismatches for checking, never read as Positive."),
    ("D17", "2026-11", "Access", "Who changes records?", "Within their assigned zones or sites (admins everywhere). Reviewers read every zone but write only where assigned. Coordinators and statisticians read and export, without writing."),
    ("D18", "2026-11", "Exports", "What do exports contain?", "Codes from the codebook; Full adds a _label column; multiple answers joined with ';'; one Screening row per regimen change; remarks included; file names end with the date in Tanzania."),
    ("D19", "2026-11", "History", "Change history?", "Every form keeps who changed which answer, when, from where and why. Correcting a saved answer needs a reason; filling an empty one doesn't."),
    ("D20", "2026-11", "Merge", "Sputum row with GeneXpert 'Not Provided' but with microscopy or culture results?", "Not merged; the rule in D01 stays. The row is listed under TB-LIS follow-up (GeneXpert: Not Provided) for CTRL to enter the GeneXpert result in TB-LIS, and merges at the next upload. Until then the EDCS record is queried."),
    ("D21", "2026-11", "Nanopore", "A Nanopore run fails and is repeated?", "Every run is recorded under 20(b): its date, the lab's run number (NN/YY, restarting each year; its year must match the run date), passed or failed with the reason, and an optional run / flow cell ID. Each participant's attempts are numbered 1, 2, 3 by date. The passing run gives the sequencing date and is the one 21 and 22 answer; while every run has failed the result is Failed (no EPI2ME queries). Exports add nanopore_runs, nanopore_first_run_date and nanopore_final_run_date, and a Nanopore runs export has one row per run (attempt, run_number, outcome, reason). Counted from 25 Nov 2026."),
]

CHANGE_LOG = [
    ("0.1", "2026-11-23", "The study team's dictionary Tanzania_data_dictionary_version_2026_11_23_EWT.xlsx as received."),
    ("0.2", "2026-11-23", "Mapping explanations corrected to match the system (see v0.2's Change log sheet)."),
    ("0.3", "2026-11-23", "Built from the system in the layout of the other study dictionaries: Summary, Forms, Data Dictionary, Choices, "
     "Mapping (Zonal Lab and TB-LIS), Decisions and Change log. Adds every form, who fills each variable, the merge rules, "
     "the decisions taken and change history."),
]


def _table(sheet, headers, rows, widths, start_row=1):
    for column, header in enumerate(headers, 1):
        cell = sheet.cell(start_row, column, header)
        cell.fill, cell.font, cell.border, cell.alignment = HEADER_FILL, HEADER_FONT, BORDER, WRAP
    for r, row in enumerate(rows, start_row + 1):
        for column, value in enumerate(row, 1):
            cell = sheet.cell(r, column, value)
            cell.border, cell.alignment = BORDER, WRAP
    for column, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    sheet.freeze_panes = sheet.cell(start_row + 1, 1)
    if rows:
        sheet.auto_filter.ref = f"A{start_row}:{get_column_letter(len(headers))}{start_row + len(rows)}"


def zonal_source(name):
    from nanopore.tblis_mapping import FIELD_RULES, NANOPORE_PREFIXES
    for names, text in ZONAL_SOURCE_RULES:
        if name in names:
            return text
    if name.startswith(NANOPORE_PREFIXES):
        return f"{DAR}: CTRL (Nanopore form). {OTHERS}: the zone's laboratory."
    if name in {rule[0] for rule in FIELD_RULES}:
        dst = name in ("phenotypic_performed", "phenotypic_date_performed") or "dst" in name or name in (
            "rifampicin", "isoniazid", "ethambutol", "levofloxacin", "bedaquiline", "linezolid", "clofazimine",
            "cycloserine", "delamanid", "pretomanid")
        if dst:
            return f"{DAR}: TB-LIS (by lab number). {OTHERS}: TB-LIS (by isolate number)."
        return f"{DAR}: TB-LIS (by lab number). {OTHERS}: the zone's laboratory."
    return f"{DAR}: not asked. {OTHERS}: the zone's laboratory."


def _choice_list(model, name):
    try:
        field = model._meta.get_field(name)
    except Exception:
        return ""
    if field.is_relation and field.related_model is not None and {"name", "value"} <= {f.name for f in field.related_model._meta.get_fields()}:
        return field.related_model.__name__
    return ""


def build_workbook():
    from reports.codebook import CODEBOOK_FORMS, codebook_version, form_codebook
    from nanopore.tblis_mapping import build_mapping, upload_rules
    from reports.data_dictionary import VERSION, VERSION_DATE

    rows, by_form, lists = [], {}, {}
    mapping = build_mapping()
    tblis_rule = {row[1]: (row[3], row[4], row[5]) for row in mapping["mapped"]}
    not_tblis = {row[1]: row[3] for row in mapping["not_mapped"]}
    for key, (title, form_class) in CODEBOOK_FORMS.items():
        model = form_class._meta.model
        for item in form_codebook(key):
            name = item["Variable name"]
            choice_list = _choice_list(model, name)
            if choice_list:
                lists[choice_list] = _choice_list_model(model, name)
            if key in ("zonal_lab", "edcs_tblis"):
                filled_by = zonal_source(name) if key == "zonal_lab" else "Rebuilt from the Zonal Lab form and TB-LIS"
                columns, rule, conversion = tblis_rule.get(name, ("", not_tblis.get(name, ""), ""))
            else:
                filled_by, columns, rule, conversion = FORMS[key][1], "", "", ""
            rows.append([len(rows) + 1, title, item["Q#"], name, item["Question label"], item["Type"], item["Required"],
                         choice_list, item["Values"], filled_by, columns, rule, conversion, item["Notes"]])
            by_form[key] = by_form.get(key, 0) + 1

    book = Workbook()
    summary = book.active
    summary.title = "Summary"
    summary["A1"] = TITLE
    summary["A1"].font = Font(bold=True, size=14, color=NAVY)
    summary["A2"] = f"Version {VERSION}, {VERSION_DATE}. Built from the system on {codebook_version()['generated']} " \
                    f"(database version {codebook_version()['database_version']})."
    lines = [
        ("Purpose", "Every variable of the study's electronic forms: label, type, codes, who fills it and, for the laboratory "
                    "forms, how TB-LIS results are merged."),
        ("Who it is for", "Data managers, statisticians, CTRL and the zonal laboratories."),
        ("How it is built", "From the forms, option lists and merge rules in use, when it is downloaded (Codebook page). "
                            "Earlier versions stay downloadable as issued."),
        ("Sheets", "Forms: each form, who completes it and how many variables. Data Dictionary: one row per variable. "
                   "Choices: the codes of every option list. Mapping: how the Zonal Lab and TB-LIS data are merged. "
                   "Decisions: what the study team decided. Change log: versions."),
        ("Zones", f"{DAR}: CTRL enters the lab number and what TB-LIS doesn't have; the results come from TB-LIS. "
                  f"{OTHERS}: the zone's laboratory enters the Zonal Lab form; CTRL gives the isolate number and TB-LIS the DST."),
        ("Change history", "Every form keeps who changed which answer, when, from where (form, CTRL, TB-LIS upload, nightly sync, "
                           "Recycle Bin) and why. Correcting a saved answer needs a reason."),
        ("Codes", "Exports give the codes listed here (column Code on Choices). Full exports add the label in a _label column; "
                  "multiple answers are joined with ';'."),
        ("No participant data", "This workbook holds variables, codes and rules only."),
    ]
    for r, (key, text) in enumerate(lines, 4):
        summary.cell(r, 1, key).font = Font(bold=True)
        summary.cell(r, 2, text).alignment = WRAP
    start = len(lines) + 6
    summary.cell(start - 1, 1, "Variables per form").font = Font(bold=True, color=NAVY)
    for r, (key, (title, _form)) in enumerate(CODEBOOK_FORMS.items(), start):
        summary.cell(r, 1, title)
        summary.cell(r, 2, by_form.get(key, 0))
    summary.column_dimensions["A"].width = 24
    summary.column_dimensions["B"].width = 110

    forms = book.create_sheet("Forms")
    _table(forms, ["Form", "Completed by", "Who and when", "Variables", "Change history"],
           [[FORMS[key][0], FORMS[key][1], FORMS[key][2], by_form.get(key, 0), "Yes"] for key in CODEBOOK_FORMS],
           [20, 60, 60, 11, 15])

    dictionary = book.create_sheet("Data Dictionary")
    _table(dictionary, ["Row", "Form", "Q#", "Variable", "Label", "Type", "Required", "Choice list", "Codes",
                        "Filled by", "TB-LIS column(s)", "Mapping rule", "TB-LIS text to code", "Notes"],
           rows, [6, 16, 7, 30, 50, 22, 9, 24, 45, 45, 26, 50, 40, 30])
    dictionary.freeze_panes = "E2"

    choices = book.create_sheet("Choices")
    choice_rows = []
    for list_name in sorted(lists):
        for option in lists[list_name].objects.order_by("value", "pk"):
            choice_rows.append([list_name, option.value, option.name])
    _table(choices, ["List", "Code", "Label"], choice_rows, [30, 8, 50])

    merge = book.create_sheet("Mapping")
    merge["A1"] = "How the Zonal Lab and TB-LIS data are merged"
    merge["A1"].font = Font(bold=True, size=12, color=NAVY)
    rules = upload_rules() + [
        ["New file and earlier results", "In the file and accepted: used. In the file and rejected: the TB-LIS values go and the record "
                                         "is listed under TB-LIS follow-up > Rejected. Not in the file: the last accepted result stays, "
                                         "marked 'Not in latest file' (exports column tblis_status)."],
        ["Nightly sync", "Every night each EDCS/TBLIS record is rebuilt from its Zonal Lab form and what TB-LIS last said, and other "
                         "zones' isolate DST is refreshed. Saving a Zonal Lab or CTRL form does the same at once."],
        ["Preview", "Shows how many records would lose TB-LIS values and how many are missing from the file, and warns when the "
                    "file is older than the last upload. Nothing is saved."],
    ]
    _table(merge, ["Topic", "Rule"], rules, [30, 120], start_row=3)
    first = len(rules) + 6
    merge.cell(first - 1, 1, "Variable by variable (EDCS / TBLIS)").font = Font(bold=True, size=12, color=NAVY)
    _table(merge, mapping["mapped_columns"], mapping["mapped"], [7, 30, 40, 30, 60, 50], start_row=first)
    merge.freeze_panes = None
    last = first + len(mapping["mapped"]) + 3
    merge.cell(last - 1, 1, "Not taken from TB-LIS").font = Font(bold=True, size=12, color=NAVY)
    _table(merge, mapping["not_mapped_columns"], mapping["not_mapped"], [7, 30, 40, 60], start_row=last)
    merge.freeze_panes = None
    merge.auto_filter.ref = None

    decisions = book.create_sheet("Decisions")
    decisions["A1"] = "Decisions taken by the study team. Add new ones in the yellow columns and send them to the data manager."
    decisions["A1"].font = Font(bold=True, color="C00000")
    _table(decisions, ["ID", "When", "Area", "Question", "Decision", "Status"],
           [[*row, "Decided"] for row in DECISIONS] + [[f"D{len(DECISIONS) + 1:02d}", "", "", "", "", "Open"]],
           [6, 10, 16, 45, 90, 10], start_row=2)
    for column in (4, 5):
        decisions.cell(len(DECISIONS) + 3, column).fill = YELLOW

    log = book.create_sheet("Change log")
    _table(log, ["Version", "Date", "Changes"], [list(row) for row in CHANGE_LOG], [9, 12, 120])
    return book


def _choice_list_model(model, name):
    return model._meta.get_field(name).related_model
