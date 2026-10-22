"""
TBLIS mapping document for the Zonal Lab / EDCS-TBLIS records.

Explains, field by field, where each EDCS/TBLIS value comes from in the TBLIS
export and how it is converted, plus the upload rules. Like the codebook it is
built at download time:
  * FIELD_RULES below holds the source columns and rule wording. Keep it next to
    the merge code: when you change apply_tblis_transformations, change the rule
    here too (nanopore/test_tblis_mapping.py fails if a merged field is missing).
  * Value conversions are read from the very mappings the upload uses, and option
    names from the option tables, so they can't drift from what really happens.
"""
import io

from django.template.loader import render_to_string

from nanopore import tasks_tblis_raw as merge
from nanopore import tblis_file
from nanopore.models import EdcsTblisZonal
from reports.codebook import codebook_version, form_codebook

DST_VALUES = "phenotypic"

# (field, TBLIS source column(s), rule, value conversion key or None)
FIELD_RULES = [
    ("unique_lab_no", "labno", "Matching key: a TBLIS row is merged into the participant whose Zonal Lab has this lab number.", None),
    ("date_sputum_received", "rctdate", "Date received.", None),
    ("appearance", "appearance_tblis, appearance", "TBLIS text converted to the appearance option.", "appearance"),
    ("sample_volume", "volume", "Volume in mL as given.", None),
    ("culture_performed", "lj_innocdate", "Yes when lj_innocdate is filled, otherwise No.", None),
    ("culture_method", "lj_innocdate, mgit_entrydate", "Checkbox: LJ when lj_innocdate is filled, MGIT when mgit_entrydate is filled, both when both.", None),
    ("microscopy_type", "fm_date, fm_res, zn_date, zn_res", "CTRL does direct-sputum microscopy: 1 = Direct sputum whenever there is a microscopy date or result.", None),
    ("microscopy_date", "fm_date, zn_date", "FM date, otherwise ZN date.", None),
    ("microscopy_results", "fm_res, zn_res", "FM result, otherwise ZN result. A result of 0 is not stored and is listed as a mismatch for a quality check.", "microscopy"),
    ("lj_inoculation_date", "lj_innocdate", "LJ inoculation date.", None),
    ("lj_results_date", "lj_date", "LJ result date.", None),
    ("lj_results", "lj_res, id_res", "TBLIS text converted to the LJ option; any other positive result without '+' is Scanty; unknown text is listed as a mismatch. id_res = 'Mycobacteria other than M.tuberculosis' makes it MOTT.", "lj"),
    ("mgit_inoculation_date", "mgit_entrydate", "MGIT entry (inoculation) date.", None),
    ("mgit_results_date", "mgit_date", "MGIT result date.", None),
    ("mgit_results", "mgit_res, id_res", "Any 'colon…' result is Positive, negative stays Negative, contaminated becomes Contamination, POSITIVE FOR NTM is MOTT. id_res = 'Mycobacteria other than M.tuberculosis' makes it MOTT.", "mgit"),
    ("phenotypic_performed", "ljdst1_date, ljdst2_date, mgitdst1_date, mgitdst2_date", "Yes when any DST result date is filled, otherwise No.", None),
    ("phenotypic_date_performed", "mgitdst1_date, mgitdst2_date, ljdst1_date, ljdst2_date", "First DST result date found, in that order.", None),
    ("first_line_dst_performed", "ljdst1_date, mgitdst1_date", "Yes when a first-line DST result date is filled, otherwise No.", None),
    ("first_line_dst_performed_date", "LJDST1_SETUPDATE", "DST set-up date. TBLIS has no set-up date for MGIT DST, so it stays empty for MGIT-only DST.", None),
    ("first_line_dst_results_date", "ljdst1_date, mgitdst1_date", "LJ result date, otherwise MGIT (same source as the results).", None),
    ("second_line_dst_performed", "ljdst2_date, mgitdst2_date", "Yes when a second-line DST result date is filled, otherwise No.", None),
    ("second_line_dst_performed_date", "LJDST2_SETUPDATE", "DST set-up date.", None),
    ("second_line_dst_results_date", "mgitdst2_date, ljdst2_date", "MGIT result date, otherwise LJ (second-line results come from MGIT).", None),
    ("rifampicin", "ljdst1_rifampicin, mgitdst1_rifampicin", "LJ result; MGIT when LJ is missing or MTB Not Detected.", DST_VALUES),
    ("isoniazid", "ljdst1_isoniazid, mgitdst1_isoniazid", "LJ result; MGIT when LJ is missing or MTB Not Detected.", DST_VALUES),
    ("ethambutol", "ljdst1_ethambutol, mgitdst1_ethambutol", "LJ result; MGIT when LJ is missing or MTB Not Detected.", DST_VALUES),
    ("levofloxacin", "mgitdst2_levofloxacin", "MGIT second-line DST result.", DST_VALUES),
    ("bedaquiline", "mgitdst2_bedaquiline", "MGIT second-line DST result.", DST_VALUES),
    ("linezolid", "mgitdst2_linezolid", "MGIT second-line DST result.", DST_VALUES),
    ("clofazimine", "mgitdst2_clofazimine", "MGIT second-line DST result.", DST_VALUES),
    ("cycloserine", "mgitdst2_cycloserine", "MGIT second-line DST result.", DST_VALUES),
    ("delamanid", "mgitdst2_delamanid", "MGIT second-line DST result.", DST_VALUES),
    ("ethionamide", "mgitdst2_ethionamide", "MGIT second-line DST result.", DST_VALUES),
    ("prothionamide", "mgitdst2_prothionamide", "MGIT second-line DST result.", DST_VALUES),
    ("para_aminosalicylic_acid", "mgitdst2_pas", "MGIT second-line DST result.", DST_VALUES),
    ("pretomanid", "mgitdst2_pretomanid", "MGIT second-line DST result. Not present in TBLIS exports so far (data dictionary: not found in TBLIS).", DST_VALUES),
    ("xpert_xdr_performed", "gxxdr_date", "Yes when gxxdr_date is filled, otherwise No.", None),
    ("xpert_xdr_date_performed", "gxxdr_date", "Xpert XDR date.", None),
    ("xpert_xdr_isoniazid", "gxxdr_isoniazid", "Converted by result name.", "xdr"),
    ("xpert_xdr_fluoroquinolones", "gxxdr_flq", "Converted by result name.", "xdr"),
    ("xpert_xdr_amikacin", "gxxdr_amikacin", "Converted by result name.", "xdr"),
    ("xpert_xdr_kanamycin", "gxxdr_kanamycin", "Converted by result name.", "xdr"),
    ("xpert_xdr_capreomycin", "gxxdr_capreomycin", "Converted by result name.", "xdr"),
    ("xpert_xdr_ethionamide", "gxxdr_ethionamide", "Converted by result name (this field has no INDETERMINATE option).", "xdr"),
    ("lpa", "lpa1_date, lpa1_mtbc, lpa2_date, lpa2_mtbc", "Yes when first- or second-line LPA was done, otherwise No.", None),
    ("first_line_lpa", "lpa1_date, lpa1_mtbc", "Yes when lpa1_date or lpa1_mtbc is filled, otherwise No.", None),
    ("first_line_lpa_date", "lpa1_date", "First-line LPA date.", None),
    ("lpa1_mtb", "lpa1_mtbc", "LPA1 MTB result.", "lpa1_mtb"),
    ("lpa1_rif", "lpa1_rifampicin", "LPA1 rifampicin result.", "lpa1_rif"),
    ("lpa1_inh", "lpa1_isoniazid", "LPA1 isoniazid result.", "lpa1_inh"),
    ("second_line_lpa", "lpa2_date, lpa2_mtbc", "Yes when lpa2_date or lpa2_mtbc is filled, otherwise No.", None),
    ("second_line_lpa_date", "lpa2_date", "Second-line LPA date.", None),
    ("lpa2_mtb", "lpa2_mtbc", "LPA2 MTB result.", "lpa1_mtb"),
    ("lpa2_rfluoroquinolones", "lpa2_flq", "LPA2 fluoroquinolones result.", "lpa2"),
    ("lpa2_aminoglycosides", "lpa2_ag_cp", "LPA2 aminoglycosides result.", "lpa2"),
    ("lpa2_kanamycin", "lpa2_low_kan", "LPA2 kanamycin result.", "lpa2"),
]

NANOPORE_REASON = "Nanopore / EPI2ME results come from a separate Excel file; not merged for now."
DISCUSSION_REASON = "Needs discussion (data dictionary); not merged."
NOT_FROM_TBLIS = {
    **{f: DISCUSSION_REASON for f in ("imipenem", "cilastatin", "meropenem", "amikacin", "streptomycin", "terizidone", "pyrazinamide")},
    "moxifloxacin": "No TBLIS mapping in the data dictionary.",
    "first_line_drugs": "LPA bands: TBLIS does not export bands.",
    "second_line_drugs": "LPA bands: TBLIS does not export bands.",
    "culture_isolate": "Information from the zonal laboratory; OK to leave empty (data dictionary).",
    "isolate_date": "Information from the zonal laboratory; OK to leave empty (data dictionary).",
    "isolate_unique_lab_no": "Information from the zonal laboratory; OK to leave empty.",
    "phenotypic_date_results": "Not mapped from TBLIS.",
    "remarks": "Free text from the Zonal Lab form.",
}
NANOPORE_PREFIXES = ("nano", "epi_to_me", "sequencing_")
DEFAULT_REASON = "Copied from the Zonal Lab record; not in TBLIS."
SKIP_FIELDS = {"id", "screening", "created_at", "created_by", "updated_at", "updated_by"}

# Value conversion key -> (mapping used by the upload, how its values are stored)
CONVERSIONS = {
    "appearance": merge.appearance_map,
    "microscopy": merge.microscopy_results_map,
    "lj": merge.lj_results_map,
    "phenotypic": merge.phenotypic_results_map,
    "xdr": merge.xpert_xdr_results_map,
    "lpa1_mtb": merge.lpa1_mtb_results_map,
    "lpa1_rif": merge.lpa1_rif_results_map,
    "lpa1_inh": merge.lpa1_inh_results_map,
    "lpa2": merge.lpa2_results_map,
}
MGIT_EXAMPLES = ["POSITIVE", "POSITIVE - 3 Colonies", "NEGATIVE", "CONTAMINATED", "Contaminated", "POSITIVE FOR NTM"]


def _option_label(field_name, stored):
    """Option text for a stored value: a pk (most maps) or an option name (Xpert XDR)."""
    if stored is None:
        return "left empty"
    options = EdcsTblisZonal._meta.get_field(field_name).related_model
    option = options.objects.filter(name__iexact=stored).first() if isinstance(stored, str) else options.objects.filter(pk=stored).first()
    if option is None:
        return f"{stored} (no such option: left empty)"
    return f"{getattr(option, 'value', option.pk)} = {option.name}"


def _conversion_text(field_name, key):
    """'Resistant, Sensitive → 2 = Susceptible; …' built from the upload's own mapping."""
    if key == "mgit":
        mapping = {text: merge.mgit_result_value(text) for text in MGIT_EXAMPLES}
    elif key:
        mapping = CONVERSIONS[key]
    else:
        return ""
    grouped = {}
    for text, stored in mapping.items():
        grouped.setdefault(stored, []).append(" ".join(text.split()))
    parts = []
    for stored, texts in grouped.items():
        shown = texts if len(texts) <= 4 else texts[:3] + [f"… ({len(texts)} texts)"]
        parts.append(f"{', '.join(shown)} → {_option_label(field_name, stored)}")
    return "; ".join(parts)


def build_mapping():
    labels = {row["Variable name"]: (row["Q#"], row["Question label"]) for row in form_codebook("edcs_tblis")}
    documented = {rule[0] for rule in FIELD_RULES}

    mapped = []
    for field, source, rule, key in FIELD_RULES:
        number, label = labels.get(field, ("", ""))
        mapped.append([number, field, label, source, rule, _conversion_text(field, key)])

    not_mapped = []
    for model_field in EdcsTblisZonal._meta.get_fields():
        name = model_field.name
        if not getattr(model_field, "concrete", False) or name in SKIP_FIELDS or name in documented:
            continue
        reason = NOT_FROM_TBLIS.get(name) or (NANOPORE_REASON if name.startswith(NANOPORE_PREFIXES) else DEFAULT_REASON)
        number, label = labels.get(name, ("", ""))
        not_mapped.append([number, name, label, reason])

    return {
        "version": codebook_version(),
        "mapped_columns": ["Q#", "Variable name", "Question label", "TBLIS source column(s)", "Rule", "Value conversion (TBLIS text → option)"],
        "mapped": mapped,
        "not_mapped_columns": ["Q#", "Variable name", "Question label", "Why it is not taken from TBLIS"],
        "not_mapped": not_mapped,
        "rules_columns": ["Topic", "Rule"],
        "rules": upload_rules(),
    }


def upload_rules():
    return [
        ["File types", "Upload the TBLIS export exactly as received: .xlsx, .xls or .csv. In Excel files the sheet with the 'labno' and 'spectype' columns is used; other sheets are ignored."],
        ["Required columns", ", ".join(tblis_file.REQUIRED_COLUMNS)],
        ["Values", "Every value is read as text, so lab numbers stay exactly as exported."],
        ["Dates", "All dates become yyyy-mm-dd. Excel dates are used as they are. In CSV files the day/month order is worked out per file (a first part above 12 means dd/mm, a second part above 12 means mm/dd); if it can't be decided the file is refused. Dates that can't be read are reported by row and lab number and left empty."],
        ["Rows used", "Only rows with spectype = Sputum AND peripheralres_genexpert starting with 'MTB Detected' or 'MTB Trace Detected'. All other rows (MTB Not Detected, Not Provided, blank, other specimens) are left out and not saved; the upload summary counts them by reason."],
        ["Who receives TBLIS values", "Dar es Salaam (CTRL) participants, PID prefixes " + ", ".join(merge.CTRL_PREFIXES) + ". Their EDCS/TBLIS record is the Zonal Lab record with the TBLIS values applied on top. Other zones' EDCS/TBLIS records are plain copies of their Zonal Lab record."],
        ["Dar es Salaam Zonal Lab form", "Only the Unique Lab Number is entered; the results come from TBLIS."],
        ["TBLIS not in EDCS", "Rows used whose lab number matches no Zonal Lab."],
        ["EDCS not in TBLIS", "Dar es Salaam EDCS/TBLIS records whose lab number is not among the rows used (including participants whose row was left out by the filter)."],
        ["Mismatches", "Every value that TBLIS changes is listed (old value → TBLIS value), plus unrecognised LJ results and microscopy results of 0."],
        ["Preview", "Runs the whole upload and shows the numbers, then rolls every change back."],
    ]


# ── output ───────────────────────────────────────────────────────────────────

def to_excel(mapping):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    workbook = Workbook()
    about = workbook.active
    about.title = "About"
    about.append(["DREAM Fund – TBLIS mapping (Zonal Lab / EDCS-TBLIS)"])
    about["A1"].font = Font(bold=True, size=14)
    about.append(["Generated", mapping["version"]["generated"]])
    about.append(["Database version", mapping["version"]["database_version"]])
    about.column_dimensions["A"].width = 22
    about.column_dimensions["B"].width = 40

    fill = PatternFill("solid", fgColor="1E3A5F")
    sheets = [
        ("Field mapping", mapping["mapped_columns"], mapping["mapped"], [6, 30, 40, 30, 50, 70]),
        ("Not from TBLIS", mapping["not_mapped_columns"], mapping["not_mapped"], [6, 30, 40, 60]),
        ("Upload rules", mapping["rules_columns"], mapping["rules"], [26, 110]),
    ]
    for title, columns, rows, widths in sheets:
        sheet = workbook.create_sheet(title)
        sheet.append(columns)
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = fill
        for row in rows:
            sheet.append(row)
        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[sheet.cell(1, index).column_letter].width = width
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        sheet.freeze_panes = "A2"

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def to_pdf(mapping):
    from weasyprint import HTML
    html = render_to_string("nanopore/laboratory/edcs_tblis/tblis_mapping_pdf.html", {"mapping": mapping})
    return HTML(string=html).write_pdf()
