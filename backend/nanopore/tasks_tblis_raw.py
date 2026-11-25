import csv
import logging
import os
import re
from decimal import Decimal, InvalidOperation
from celery import shared_task
from django.apps import apps
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from nanopore.models import (
    EdcsTblisMergeSummary,
    EdcsTblisZonal,
    TblisRawData,
    TblisUploadBatch,
    ZonalLaboratory,
)
from nanopore import history, tblis_status
from nanopore.models.discrepancies import (
    TblisFollowUp, TblisNotInEdcs, EdcsNotInTblis, EdcsTblisMismatch, TblisIsolateDst, TblisLeftOut,
)
from nanopore.zonal_rules import CTRL_FIELDS, LAB_NUMBER_ONLY_Q
from options.models import (
    SampleAppearance, YesNo, CultureMethod, MicroscopyType, CultureMicroscopyResults,
    LJCultureResult, MGITCultureResult, YesNoNA, PhenotypicDSTResults,
    XpertXDRResults, XpertXDRResultsTwo, XpertXDRResultsThree,
    FirstLineDrugs, SecondLineDrugs,
    MTBResultsLPA, RIFResultLPA, INHResultLPA, NanoporeResults,
    NanoporeSequencingResults, NanoporeSequencingDelayedReasons
)

from nanopore.substudy4_set_aside import set_aside_lab_numbers
from nanopore.tblis_file import (
    FILTER_REASONS, MAX_REPORTED_PROBLEMS, TblisFileError, filter_reason, filter_rows, follow_up_rows, is_isolate,
    read_tblis_file,
)
# Helper functions from utils or duplicated logic (simplified for chunk processing)
from utils.edcs_tblis_helpers import safe_int, safe_decimal, parse_date_field, get_foreign, split_m2m

logger = logging.getLogger(__name__)

# --- MODULE LEVEL MAPPINGS ---
appearance_map = {
    "Salivary": 1, "Clear": 1, "Colourless": 1, "Mucosalivary": 1,
    "Mucoid": 2, "Purulent": 3, "Turbid": 3, "Mucopurulent": 4,
    "Bloody": 5, "Mucopurulent / Bloody": 5,
    "Not Applicable": 6, "Not Indicated": 6, "See Comment": 6, "Brown": 6
}

microscopy_results_map = {
    "NEGATIVE - No AFBs seen": 1,
    **dict.fromkeys([
        "POSITIVE   1 AFBs / Length Seen","POSITIVE   2 AFBs / Length Seen","POSITIVE   3 AFBs / Length Seen","POSITIVE   4 AFBs / Length Seen","POSITIVE   5 AFBs / Length Seen",
        "POSITIVE   6 AFBs / Length Seen","POSITIVE   7 AFBs / Length Seen","POSITIVE   8 AFBs / Length Seen","POSITIVE   9 AFBs / Length Seen","POSITIVE   10 AFBs / Length Seen",
        "POSITIVE   11 AFBs / Length Seen","POSITIVE   12 AFBs / Length Seen","POSITIVE   13 AFBs / Length Seen","POSITIVE   14 AFBs / Length Seen","POSITIVE   15 AFBs / Length Seen",
        "POSITIVE   16 AFBs / Length Seen","POSITIVE   17 AFBs / Length Seen","POSITIVE   18 AFBs / Length Seen","POSITIVE   19 AFBs / Length Seen",
    ], 2),
    "POSITIVE   1+ AFBs Seen": 3,
    "POSITIVE   2+ AFBs Seen": 4,
    "POSITIVE   3+ AFBs Seen": 5,
    **dict.fromkeys([
        "POSITIVE - 1 AFBs/100 fields seen","POSITIVE - 2 AFBs/100 fields seen","POSITIVE - 3 AFBs/100 fields seen","POSITIVE - 4 AFBs/100 fields seen","POSITIVE - 5 AFBs/100 fields seen",
        "POSITIVE - 6 AFBs/100 fields seen","POSITIVE - 7 AFBs/100 fields seen","POSITIVE - 8 AFBs/100 fields seen","POSITIVE - 9 AFBs/100 fields seen",
        "POSITIVE   20 AFBs / Length Seen","POSITIVE   21 AFBs / Length Seen","POSITIVE   22 AFBs / Length Seen","POSITIVE   23 AFBs / Length Seen","POSITIVE   24 AFBs / Length Seen","POSITIVE   25 AFBs / Length Seen",
        "POSITIVE   26 AFBs / Length Seen","POSITIVE   27 AFBs / Length Seen","POSITIVE   28 AFBs / Length Seen","POSITIVE   29 AFBs / Length Seen","POSITIVE   30 AFBs / Length Seen",
    ], 6),
}

lj_results_map = {
    **dict.fromkeys([
        f"POSITIVE - {i} {'Colony' if i==1 else 'Colonies'}" for i in range(1, 51)
    ], 1),
    "POSITIVE - 1+ Colonies": 2,
    "POSITIVE - 2+ Colonies": 3, "POSITIVE - More than 20 Colonies": 3,
    "POSITIVE - 3+ Colonies": 4, "POSITIVE": 4, "POSITIVE - Confluent Growth": 4, "POSITIVE - Innumerable Colonies": 4,
    "NEGATIVE": 5,
    "CONTAMINATED": 6,
    "POSITIVE   4+ AFBs Seen": 8,
}

mgit_results_map = {
    "POSITIVE": 1, "NEGATIVE": 2, "Contaminated": 3, "POSITIVE FOR NTM": 4
}

MOTT_ID_RESULT = "mycobacteria other than m.tuberculosis"
LJ_MOTT, MGIT_MOTT = 7, 4


_LJ_RESULTS_BY_TEXT = {" ".join(k.split()).upper(): v for k, v in lj_results_map.items()}
LJ_SCANTY = 1


def lj_result_value(text):
    """
    LJ culture result (data dictionary): known TBLIS texts map directly; any other
    positive result without a "+" is Scanty. Returns (value, recognised).
    """
    if not text:
        return None, True
    normalized = " ".join(text.split()).upper()
    if normalized in _LJ_RESULTS_BY_TEXT:
        return _LJ_RESULTS_BY_TEXT[normalized], True
    if normalized.startswith("POSITIVE") and "+" not in normalized:
        return LJ_SCANTY, True
    return None, False


def is_mott(id_res):
    """Culture identification says MOTT. Only this exact result counts (not "Negative")."""
    return bool(id_res) and id_res.strip().lower() == MOTT_ID_RESULT


def mgit_result_value(text):
    """
    MGIT result (data dictionary): any "colon..." result is Positive, negative stays
    Negative, contaminated becomes Contamination, POSITIVE FOR NTM is MOTT.
    "No colonies", "Nil", "0 colonies" and unknown texts give None: the merge lists them.
    """
    value = (text or "").strip().lower()
    if not value:
        return None
    if re.match(r"(no|nil|none|zero|0)\b", value):
        return None
    if value == "positive for ntm":
        return MGIT_MOTT
    if "contaminat" in value:
        return 3
    if value.startswith("negative"):
        return 2
    if "colon" in value or value.startswith("positive"):
        return 1
    return None

# Phenotypic DST (options: 1 Resistant, 2 Susceptible, 3 Contaminated, 4 Invalid,
# 5 Not Done). Follows the data dictionary EDCS sheet: Indeterminate -> 4 Invalid,
# MTB Not Detected -> 5 Not done (the "DST result map" sheet says invalid; the
# EDCS sheet was chosen).
phenotypic_results_map = {
    "Resistance Detected": 1, "Resistance Inferred": 1, "Resistant": 1,
    "Resistance not Detected": 2, "Sensitive": 2,
    "Indeterminate": 4, "Resistance Indeterminate": 4,
    "MTB Not Detected": 5,
}

# Xpert XDR: TBLIS result -> option NAME. The three XDR option tables number
# their options differently (and pk != value in two of them), so options are
# looked up by name. TBLIS never reports "Low Resistance DETECTED", and
# "MTB Not Detected" (dictionary: 0) has no option, so it stays empty.
xpert_xdr_results_map = {
    "Resistance Detected": "Resistance DETECTED",
    "Resistance Inferred": "Resistance DETECTED",
    "Resistant": "Resistance DETECTED",
    "Resistance not Detected": "Resistance NOT DETECTED",
    "Sensitive": "Resistance NOT DETECTED",
    "Indeterminate": "Resistance INDETERMINATE",
    "Resistance Indeterminate": "Resistance INDETERMINATE",
}

lpa1_mtb_results_map = {"MTBC Detected": 1, "MTBC Not Detected": 2, "Invalid": 3}
lpa1_rif_results_map = {
    "Resistance Detected": 1, "Resistant": 1,
    "Resistance not Detected": 2, "Sensitive": 2,
    "Indeterminate": 3, "Resistance Indeterminate": 3,
    "Resistance Inferred": 4, "MTB Not Detected": None
}
lpa1_inh_results_map = {
    "Resistance Detected": 1, "Resistant": 1,
    "Resistance not Detected": 3, "Sensitive": 3,
    "Resistance Indeterminate": 4, "Indeterminate": 4,
    "Resistance Inferred": 5, "MTB Not Detected": None
}
lpa2_mtb_results_map = {"MTBC Detected": 1, "MTBC Not Detected": 2, "Invalid": 3}
lpa2_results_map = {
    "Resistance Detected": 1, "Resistant": 1,
    "Resistance not Detected": 2, "Sensitive": 2,
    "Indeterminate": 3, "Resistance Indeterminate": 3,
    "Resistance Inferred": 4, "MTB Not Detected": None
}

NA_VALUE = 98  # the "Na" answer of Yes/No/Na questions (codebook)

CTRL_PREFIXES = [
    "DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16",
    "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19"
]

# DST answers the site may enter and an isolate row may also fill
SITE_DST_COLUMNS = {
    "ethionamide": "mgitdst2_ethionamide",
    "prothionamide": "mgitdst2_prothionamide",
    "para_aminosalicylic_acid": "mgitdst2_pas",
}


def get_ctrl_prefix_query():
    prefix_query = Q()
    for prefix in CTRL_PREFIXES:
        prefix_query |= Q(screening__pid__startswith=prefix)
    return prefix_query

# --- TRANSFORMATION LOGIC ---
def mismatch_logger(record, labno):
    """log_mismatch(field, old, new): records where the form and TBLIS disagree."""
    def same_value(old_val, new_val):
        try:  # numbers: 2.0 and "2" are the same volume
            return Decimal(str(old_val).strip()) == Decimal(str(new_val).strip())
        except (InvalidOperation, ValueError):
            return str(old_val).strip() == str(new_val).strip()

    def log_mismatch(field, old_val, new_val):
        if old_val and new_val and not same_value(old_val, new_val):
            pid = record.screening.pid if hasattr(record, 'screening') and record.screening else None
            EdcsTblisMismatch.objects.create(
                labno=labno, pid=pid, field_name=field, 
                edcs_value=str(old_val), tblis_value=str(new_val)
            )
    return log_mismatch


def apply_tblis_dst(edcs_zonal, clean_row, log_mismatch, keep_unanswered=False):
    """
    The phenotypic DST section of a TBLIS row: performed, dates and results (data dictionary 12-14).
    "Performed" is Yes when there is a DST date; without one it is empty, or, with
    keep_unanswered (another zone's form), the site's own answer stays.
    """
    def performed(name, done):
        if done:
            log_mismatch(name, getattr(edcs_zonal, name), 1)
            setattr(edcs_zonal, name, 1)
        elif not keep_unanswered:
            setattr(edcs_zonal, name, None)

    # Phenotypic DST Date
    mgitdst1_date = clean_row.get("mgitdst1_date")
    mgitdst2_date = clean_row.get("mgitdst2_date")
    ljdst1_date = clean_row.get("ljdst1_date")
    ljdst2_date = clean_row.get("ljdst2_date")
    
    # DST set-up dates (the day the DST was performed). TBLIS only has them for LJ.
    ljdst1_setupdate = clean_row.get("LJDST1_SETUPDATE")
    ljdst2_setupdate = clean_row.get("LJDST2_SETUPDATE")
    
    pheno_date = ljdst1_date or mgitdst1_date or ljdst2_date or mgitdst2_date
    performed("phenotypic_performed_id", pheno_date)
    if pheno_date:
        parsed_pheno_date = parse_date_field(pheno_date)
        log_mismatch("phenotypic_date_performed", edcs_zonal.phenotypic_date_performed, parsed_pheno_date)
        edcs_zonal.phenotypic_date_performed = parsed_pheno_date

    # First and Second Line DST Performed (data dictionary): performed when there is
    # a DST result date. The performed DATE is the LJ set-up date; without one, MGIT:
    # its DST entry date, else its result date (TBLIS has no MGIT set-up date and
    # has so far left the entry date empty).
    first_line_perf_date = ljdst1_setupdate or clean_row.get("mgitdst1_entrydate") or mgitdst1_date
    performed("first_line_dst_performed_id", ljdst1_date or mgitdst1_date)
    if first_line_perf_date:
        parsed_first_perf = parse_date_field(first_line_perf_date)
        log_mismatch("first_line_dst_performed_date", edcs_zonal.first_line_dst_performed_date, parsed_first_perf)
        edcs_zonal.first_line_dst_performed_date = parsed_first_perf

    second_line_perf_date = ljdst2_setupdate or clean_row.get("mgitdst2_entrydate") or mgitdst2_date
    performed("second_line_dst_performed_id", ljdst2_date or mgitdst2_date)
    if second_line_perf_date:
        parsed_second_perf = parse_date_field(second_line_perf_date)
        log_mismatch("second_line_dst_performed_date", edcs_zonal.second_line_dst_performed_date, parsed_second_perf)
        edcs_zonal.second_line_dst_performed_date = parsed_second_perf


    # First and Second Line DST Results Dates (data dictionary 12e, 12h): LJ, otherwise MGIT.
    first_line_res_date = ljdst1_date or mgitdst1_date
    if first_line_res_date:
        parsed_first_res = parse_date_field(first_line_res_date)
        log_mismatch("first_line_dst_results_date", edcs_zonal.first_line_dst_results_date, parsed_first_res)
        edcs_zonal.first_line_dst_results_date = parsed_first_res

    second_line_res_date = ljdst2_date or mgitdst2_date
    if second_line_res_date:
        parsed_second_res = parse_date_field(second_line_res_date)
        log_mismatch("second_line_dst_results_date", edcs_zonal.second_line_dst_results_date, parsed_second_res)
        edcs_zonal.second_line_dst_results_date = parsed_second_res

    # Phenotypic DST Results
    def apply_dst(edcs_field, tblis_col, override_col=None):
        tblis_str = clean_row.get(tblis_col)
        override_str = clean_row.get(override_col) if override_col else None
        
        val = phenotypic_results_map.get(tblis_str) if tblis_str else None
        if override_str:
            over_val = phenotypic_results_map.get(override_str)
            if over_val and (not val or val == 5):
                val = over_val
                
        if val:
            existing = getattr(edcs_zonal, f"{edcs_field}_id", None)
            log_mismatch(edcs_field, existing, val)
            setattr(edcs_zonal, f"{edcs_field}_id", val)

    apply_dst("rifampicin", "ljdst1_rifampicin", "mgitdst1_rifampicin")
    apply_dst("isoniazid", "ljdst1_isoniazid", "mgitdst1_isoniazid")
    apply_dst("levofloxacin", "mgitdst2_levofloxacin")
    apply_dst("bedaquiline", "mgitdst2_bedaquiline")
    apply_dst("linezolid", "mgitdst2_linezolid")
    apply_dst("clofazimine", "mgitdst2_clofazimine")
    apply_dst("cycloserine", "mgitdst2_cycloserine")
    apply_dst("ethambutol", "ljdst1_ethambutol", "mgitdst1_ethambutol")
    apply_dst("delamanid", "mgitdst2_delamanid")
    apply_dst("ethionamide", "mgitdst2_ethionamide")
    apply_dst("prothionamide", "mgitdst2_prothionamide")
    apply_dst("para_aminosalicylic_acid", "mgitdst2_pas")
    apply_dst("pretomanid", "mgitdst2_pretomanid")


def _plain(value):
    """A field value as the JSON record of TB-LIS's DST keeps it."""
    return value.isoformat() if hasattr(value, "isoformat") else value


def _isolate_dst_fields():
    names = (*CTRL_FIELDS[1:], "phenotypic_date_performed", *SITE_DST_COLUMNS)
    return [ZonalLaboratory._meta.get_field(name) for name in names]


def _take_back_dst(z_lab, values):
    """Put back what the form had before TB-LIS, unless the site has changed the answer since."""
    for field in _isolate_dst_fields():
        if field.attname in values:
            given, before = values[field.attname]
            if _plain(getattr(z_lab, field.attname)) == given:
                setattr(z_lab, field.attname, before if field.is_relation else field.to_python(before))


def _isolate_source(z_lab, before_row=None):
    """
    What TB-LIS gave this form by its current number. DST merged before that was
    recorded: an answer equal to what a stored row of this number gives came from it.
    before_row: the row being merged now, which can't have given anything yet.
    """
    number = z_lab.isolate_unique_lab_no
    source = TblisIsolateDst.objects.filter(zonal_lab=z_lab).first()
    if source and source.number == number:
        return source
    if source:  # the number was changed outside CTRL's form
        _take_back_dst(z_lab, source.values)
    else:
        source = TblisIsolateDst(zonal_lab=z_lab)
    source.number, source.values, source.before_known = number, {}, False

    stored = TblisRawData.objects.filter(labno=number, raw_data__spectype__iexact="isolate")
    if before_row:
        stored = stored.filter(pk__lt=before_row)
    fields = _isolate_dst_fields()
    for row in stored.values_list("raw_data", flat=True):
        gives = ZonalLaboratory()
        apply_tblis_dst(gives, row, lambda *args: None)
        for field in fields:
            value = getattr(gives, field.attname)
            if value is not None and value == getattr(z_lab, field.attname):
                source.values[field.attname] = [_plain(value), None]
    return source


def merge_isolate_dst(z_lab, clean_row, raw_id=None):
    """
    Another zone's isolate: CTRL's TBLIS row gives the DST section of its Zonal Lab
    form, saved there so the daily sync carries it to EDCS/TBLIS. The other sections
    stay as the site entered them.

    It starts from what the form had before TB-LIS, so a blank in TB-LIS takes back
    only what TB-LIS gave, and a No doesn't undo the site's own Yes.
    clean_row None: TB-LIS rejects the number now, so all it gave goes.
    """
    fields = _isolate_dst_fields()
    shown = {field.attname: getattr(z_lab, field.attname) for field in fields}
    source = _isolate_source(z_lab, raw_id)
    _take_back_dst(z_lab, source.values)
    before = {field.attname: getattr(z_lab, field.attname) for field in fields}
    if clean_row is not None:
        apply_tblis_dst(z_lab, clean_row, lambda *args: None, keep_unanswered=True)

    log_mismatch = mismatch_logger(z_lab, z_lab.isolate_unique_lab_no)
    source.values = {}
    for name, was in before.items():
        value = getattr(z_lab, name)
        if value != was:
            source.values[name] = [_plain(value), _plain(was)]
        if value != shown[name]:
            log_mismatch(name, shown[name], value)
    with transaction.atomic():
        z_lab.save()
        source.save()


def clear_isolate_dst(z_lab, old_number):
    """
    The isolate number was changed or cleared: the DST that came by the old number is
    another isolate's, so the site's own answers come back. When those weren't recorded
    the DST section is cleared; drugs the site also enters go only if the old number's rows had them.
    """
    source = TblisIsolateDst.objects.filter(zonal_lab=z_lab, number=old_number).first()
    if source:
        _take_back_dst(z_lab, source.values)
        if source.before_known:
            return
    for name in (*CTRL_FIELDS[1:], "phenotypic_date_performed"):
        setattr(z_lab, name, None)
    old_rows = list(TblisRawData.objects.filter(labno=old_number, raw_data__spectype__iexact="isolate")
                    .values_list("raw_data", flat=True))
    for name, column in SITE_DST_COLUMNS.items():
        if any(row.get(column) for row in old_rows):
            setattr(z_lab, name, None)


def start_isolate_dst(z_lab):
    """A number was just entered, changed or cleared: what's on the form now is the site's own."""
    if z_lab.isolate_unique_lab_no:
        TblisIsolateDst.objects.update_or_create(
            zonal_lab=z_lab, defaults={"number": z_lab.isolate_unique_lab_no, "values": {}, "before_known": True},
        )
    else:
        TblisIsolateDst.objects.filter(zonal_lab=z_lab).delete()


def merge_isolate_from_raw(z_lab):
    """Apply what TB-LIS last said about this form's isolate number. True when it has an isolate row for it."""
    found = tblis_status.status(z_lab.isolate_unique_lab_no, isolate=True)
    if found.used:
        merge_isolate_dst(z_lab, TblisRawData.objects.get(pk=found.raw_id).raw_data)
    elif found.state:
        merge_isolate_dst(z_lab, None)
    return found.used


def apply_tblis_transformations(edcs_zonal, clean_row, labno):
    """
    Applies all TBLIS specific mapping transformations directly to the EdcsTblisZonal object,
    overwriting fields where TBLIS data is present and logging mismatches.
    """
    log_mismatch = mismatch_logger(edcs_zonal, labno)

    # Appearance mapping
    app_str = clean_row.get("appearance_tblis") or clean_row.get("appearance")
    app_val = appearance_map.get(app_str) if app_str else None
    if app_val:
        log_mismatch("appearance", edcs_zonal.appearance_id, app_val)
        edcs_zonal.appearance_id = app_val

    # Date of sputum received (rctdate)
    rctdate = clean_row.get("rctdate")
    if rctdate:
        parsed_date = parse_date_field(rctdate)
        log_mismatch("date_sputum_received", edcs_zonal.date_sputum_received, parsed_date)
        edcs_zonal.date_sputum_received = parsed_date

    # Culture logic: if LJ innocdate exists, culture performed is 1, else 2
    lj_date = clean_row.get("lj_innocdate")
    culture_val = 1 if (lj_date or clean_row.get("mgit_entrydate")) else 2  # data dictionary 6a: LJ, else MGIT
    log_mismatch("culture_performed_id", edcs_zonal.culture_performed_id, culture_val)
    edcs_zonal.culture_performed_id = culture_val

    # Sample volume
    vol_str = clean_row.get("volume")
    if vol_str:
        log_mismatch("sample_volume", edcs_zonal.sample_volume, vol_str)
        edcs_zonal.sample_volume = vol_str

    # Microscopy dates and results
    fm_date = clean_row.get("fm_date")
    zn_date = clean_row.get("zn_date")
    mic_date_str = fm_date or zn_date
    
    fm_res = clean_row.get("fm_res")
    zn_res = clean_row.get("zn_res")
    mic_res_str = fm_res or zn_res
    mic_res_val = microscopy_results_map.get(mic_res_str) if mic_res_str else None
    if mic_res_str and mic_res_str.strip() == "0":
        # Data dictionary: a microscopy result of 0 needs a quality check, so it is
        # not stored; it is listed with the mismatches for the lab to confirm.
        mic_res_val = None
        EdcsTblisMismatch.objects.create(
            labno=labno, pid=edcs_zonal.screening.pid if edcs_zonal.screening_id else None,
            field_name="microscopy_results (0 - needs quality check)",
            edcs_value=str(edcs_zonal.microscopy_results_id or ""), tblis_value=mic_res_str,
        )
    
    # Microscopy type: CTRL does direct-sputum microscopy (ZN or FM), so any
    # microscopy result is 1 = Direct sputum (data dictionary, microscopy_type).
    mic_type_val = 1 if (zn_date or zn_res or fm_date or fm_res) else None
        
    if mic_type_val:
        log_mismatch("microscopy_type_id", edcs_zonal.microscopy_type_id, mic_type_val)
        edcs_zonal.microscopy_type_id = mic_type_val
        
    if mic_date_str:
        parsed_mic_date = parse_date_field(mic_date_str)
        log_mismatch("microscopy_date", edcs_zonal.microscopy_date, parsed_mic_date)
        edcs_zonal.microscopy_date = parsed_mic_date
        
    if mic_res_val:
        log_mismatch("microscopy_results_id", edcs_zonal.microscopy_results_id, mic_res_val)
        edcs_zonal.microscopy_results_id = mic_res_val

    # Culture Method is a checkbox question (1 = LJ, 2 = MGIT): tick every method
    # that was done, so both when both were inoculated.
    mgit_entry = clean_row.get("mgit_entrydate")
    cm_vals = sorted(([1] if lj_date else []) + ([2] if mgit_entry else []))

    if cm_vals:
        existing_cm = sorted(edcs_zonal.culture_method.values_list('id', flat=True))
        log_mismatch("culture_method", ",".join(map(str, existing_cm)), ",".join(map(str, cm_vals)))
        edcs_zonal.culture_method.set(cm_vals)

    # LJ Culture
    if lj_date:
        parsed_lj_date = parse_date_field(lj_date)
        log_mismatch("lj_inoculation_date", edcs_zonal.lj_inoculation_date, parsed_lj_date)
        edcs_zonal.lj_inoculation_date = parsed_lj_date
        
    lj_res_date = clean_row.get("lj_date")
    if lj_res_date:
        parsed_lj_res_date = parse_date_field(lj_res_date)
        log_mismatch("lj_results_date", edcs_zonal.lj_results_date, parsed_lj_res_date)
        edcs_zonal.lj_results_date = parsed_lj_res_date
        
    id_res = clean_row.get("id_res")
    lj_res_str = clean_row.get("lj_res")
    lj_res_val, lj_recognised = lj_result_value(lj_res_str)
    if not lj_recognised:
        # Unknown LJ text: left empty and listed with the mismatches for review.
        EdcsTblisMismatch.objects.create(
            labno=labno, pid=edcs_zonal.screening.pid if edcs_zonal.screening_id else None,
            field_name="lj_results (unrecognised TBLIS value)",
            edcs_value=str(edcs_zonal.lj_results_id or ""), tblis_value=lj_res_str,
        )
    
    # Override rule: an identification of "Mycobacteria other than M.tuberculosis"
    # makes the LJ result MOTT (only when an LJ culture was done).
    if is_mott(id_res) and (lj_res_str or lj_date):
        lj_res_val = LJ_MOTT
        
    if lj_res_val:
        log_mismatch("lj_results_id", edcs_zonal.lj_results_id, lj_res_val)
        edcs_zonal.lj_results_id = lj_res_val

    # MGIT Culture
    if mgit_entry:
        parsed_mgit_entrydate = parse_date_field(mgit_entry)
        log_mismatch("mgit_inoculation_date", edcs_zonal.mgit_inoculation_date, parsed_mgit_entrydate)
        edcs_zonal.mgit_inoculation_date = parsed_mgit_entrydate

    mgit_date = clean_row.get("mgit_date")
    if mgit_date:
        parsed_mgit_date = parse_date_field(mgit_date)
        log_mismatch("mgit_results_date", edcs_zonal.mgit_results_date, parsed_mgit_date)
        edcs_zonal.mgit_results_date = parsed_mgit_date
        
    mgit_res_str = clean_row.get("mgit_res")
    mgit_res_val = mgit_result_value(mgit_res_str)
    if mgit_res_str and mgit_res_val is None:
        # Unknown MGIT text: left empty and listed with the mismatches for review, like LJ.
        EdcsTblisMismatch.objects.create(
            labno=labno, pid=edcs_zonal.screening.pid if edcs_zonal.screening_id else None,
            field_name="mgit_results (unrecognised TBLIS value)",
            edcs_value=str(edcs_zonal.mgit_results_id or ""), tblis_value=mgit_res_str,
        )
    # Same MOTT rule as LJ (only when an MGIT culture was done).
    if is_mott(id_res) and (mgit_res_str or mgit_entry):
        mgit_res_val = MGIT_MOTT
    if mgit_res_val:
        log_mismatch("mgit_results_id", edcs_zonal.mgit_results_id, mgit_res_val)
        edcs_zonal.mgit_results_id = mgit_res_val

    apply_tblis_dst(edcs_zonal, clean_row, log_mismatch)
    
    # Xpert XDR performed: Yes when TBLIS has gxxdr_date, otherwise No (same as
    # DST and LPA performed).
    gxxdr_date = clean_row.get("gxxdr_date")
    if gxxdr_date:
        parsed_xpert_date = parse_date_field(gxxdr_date)
        log_mismatch("xpert_xdr_date_performed", edcs_zonal.xpert_xdr_date_performed, parsed_xpert_date)
        edcs_zonal.xpert_xdr_date_performed = parsed_xpert_date
    xpert_performed_val = 1 if gxxdr_date else 2
    log_mismatch("xpert_xdr_performed_id", edcs_zonal.xpert_xdr_performed_id, xpert_performed_val)
    edcs_zonal.xpert_xdr_performed_id = xpert_performed_val

    def apply_xdr(edcs_field, tblis_col):
        tblis_str = clean_row.get(tblis_col)
        option_name = xpert_xdr_results_map.get(tblis_str) if tblis_str else None
        if not option_name:
            return
        options = EdcsTblisZonal._meta.get_field(edcs_field).related_model
        option = options.objects.filter(name__iexact=option_name).first()
        if option is None:  # e.g. ethionamide has no INDETERMINATE option
            return
        existing = getattr(edcs_zonal, f"{edcs_field}_id", None)
        log_mismatch(edcs_field, existing, option.pk)
        setattr(edcs_zonal, f"{edcs_field}_id", option.pk)
            
    apply_xdr("xpert_xdr_isoniazid", "gxxdr_isoniazid")
    apply_xdr("xpert_xdr_fluoroquinolones", "gxxdr_flq")
    apply_xdr("xpert_xdr_amikacin", "gxxdr_amikacin")
    apply_xdr("xpert_xdr_kanamycin", "gxxdr_kanamycin")
    apply_xdr("xpert_xdr_capreomycin", "gxxdr_capreomycin")
    apply_xdr("xpert_xdr_ethionamide", "gxxdr_ethionamide")
    
    # LPA conducted and dates (TBLIS has lpa1_date / lpa2_date). A line counts as
    # done when it has a date or an MTB result; no LPA in TBLIS means No.
    # The band checkboxes can't be filled: TBLIS doesn't export bands.
    lpa1_done = bool(clean_row.get("lpa1_date") or clean_row.get("lpa1_mtbc"))
    lpa2_done = bool(clean_row.get("lpa2_date") or clean_row.get("lpa2_mtbc"))
    for field, done in (("first_line_lpa", lpa1_done), ("second_line_lpa", lpa2_done),
                        ("lpa", lpa1_done or lpa2_done)):
        value = 1 if done else 2
        log_mismatch(f"{field}_id", getattr(edcs_zonal, f"{field}_id"), value)
        setattr(edcs_zonal, f"{field}_id", value)
    for field, column in (("first_line_lpa_date", "lpa1_date"), ("second_line_lpa_date", "lpa2_date")):
        if clean_row.get(column):
            parsed = parse_date_field(clean_row[column])
            log_mismatch(field, getattr(edcs_zonal, field), parsed)
            setattr(edcs_zonal, field, parsed)

    # First-line and Second-line LPA results
    def apply_lpa(edcs_field, tblis_col, mapping_dict, is_m2m=False):
        tblis_str = clean_row.get(tblis_col)
        val = mapping_dict.get(tblis_str) if tblis_str else None
        if val:
            if is_m2m:
                existing_list = list(getattr(edcs_zonal, edcs_field).values_list('id', flat=True))
                old_str = str(existing_list[0]) if existing_list else ""
                log_mismatch(edcs_field, old_str, str(val))
                getattr(edcs_zonal, edcs_field).set([val])
            else:
                existing = getattr(edcs_zonal, f"{edcs_field}_id", None)
                log_mismatch(edcs_field, existing, val)
                setattr(edcs_zonal, f"{edcs_field}_id", val)
            
    apply_lpa("lpa1_mtb", "lpa1_mtbc", lpa1_mtb_results_map)
    apply_lpa("lpa1_rif", "lpa1_rifampicin", lpa1_rif_results_map)
    apply_lpa("lpa1_inh", "lpa1_isoniazid", lpa1_inh_results_map, is_m2m=True)
    
    apply_lpa("lpa2_mtb", "lpa2_mtbc", lpa2_mtb_results_map)
    apply_lpa("lpa2_rfluoroquinolones", "lpa2_flq", lpa2_results_map)
    apply_lpa("lpa2_aminoglycosides", "lpa2_ag_cp", lpa2_results_map)
    apply_lpa("lpa2_kanamycin", "lpa2_low_kan", lpa2_results_map)


def sync_zonal_laboratory_to_edcs(z_lab, clean_row=None):
    """
    Syncs a ZonalLaboratory record to EdcsTblisZonal.
    If clean_row is provided (TBLIS data), it additionally applies TBLIS transformations over it.
    """
    e_zonal = EdcsTblisZonal.objects.filter(screening=z_lab.screening).first()
    if not e_zonal:
        e_zonal = EdcsTblisZonal(screening=z_lab.screening)
        
    with history.one_change(e_zonal):
        return _rebuild_edcs(e_zonal, z_lab, clean_row)


def _rebuild_edcs(e_zonal, z_lab, clean_row):
    e_zonal.unique_lab_no = z_lab.unique_lab_no or f"SYNC-{z_lab.screening.pid}"
    
    # Copy all standard fields exactly as-is
    exclude_fields = ['id', 'screening', 'created_at', 'created_by', 'updated_at', 'updated_by']
    for field in ZonalLaboratory._meta.fields:
        if field.name not in exclude_fields:
            val = getattr(z_lab, field.name)
            setattr(e_zonal, field.name, val)
    if z_lab.screening.pid.startswith(tuple(CTRL_PREFIXES)):
        # Dar es Salaam: CTRL cultures every sample and TB-LIS merges by lab number,
        # so question 11 (isolate sent, its date and number) is Na.
        e_zonal.culture_isolate = YesNoNA.objects.filter(value=NA_VALUE).first()
        e_zonal.isolate_date = None
        e_zonal.isolate_unique_lab_no = None
    e_zonal.save()
    
    # Copy ManyToMany fields exactly as-is
    for m2m_field in ZonalLaboratory._meta.many_to_many:
        if m2m_field.name not in exclude_fields:
            z_m2m = getattr(z_lab, m2m_field.name).all()
            getattr(e_zonal, m2m_field.name).set(z_m2m)

    # If we have TBLIS data (because this is a Zonal record), overlay the transformations!
    if clean_row:
        apply_tblis_transformations(e_zonal, clean_row, z_lab.unique_lab_no)
        e_zonal.save()
        
    return e_zonal


def sync_with_latest_tblis(z_lab):
    """Rebuild the EDCS/TBLIS record from the Zonal Lab form and what TBLIS last said (nanopore/tblis_status.py)."""
    clean_row = None
    if any(z_lab.screening.pid.startswith(prefix) for prefix in CTRL_PREFIXES):
        found = tblis_status.status(z_lab.unique_lab_no)
        if found.used:
            clean_row = TblisRawData.objects.get(pk=found.raw_id).raw_data
    else:
        merge_isolate_from_raw(z_lab)
    return sync_zonal_laboratory_to_edcs(z_lab, clean_row)


# --- CELERY TASKS ---
class _PreviewRollback(Exception):
    """Raised at the end of a preview so every database change is rolled back."""

    def __init__(self, result):
        super().__init__("preview")
        self.result = result


@shared_task(bind=True)
def process_raw_tblis_upload(self, filepath, user_id=None, source_filename=None, dry_run=False):
    """
    Reads a raw TBLIS export (.xlsx, .xls or .csv), keeps only the rows the study
    uses (see nanopore/tblis_file.py), saves them to TblisRawData and merges
    matching records into EdcsTblisZonal.

    dry_run=True is the Preview: everything runs exactly the same, then all
    database changes are rolled back and only the numbers are returned.
    """
    source_filename = source_filename or os.path.basename(filepath)
    # Tell the page at once that the worker has it: reading a full file takes a while
    self.update_state(state="PROGRESS", meta={"current": 0, "total": 0, "stage": "Reading the file"})
    try:
        prepared = read_tblis_file(filepath)
    except TblisFileError as exc:
        return {"state": "SUCCESS", "file_error": str(exc), "preview": dry_run, "errors": []}

    kept_rows, left_out = filter_rows(prepared["rows"])
    # A file older than the last upload would become the latest and undo newer results
    latest = TblisUploadBatch.objects.first()
    file_newest = max((row.get("rctdate", "")[:10] for row in kept_rows), default="")
    latest_newest = max((str(d or "")[:10] for d in TblisRawData.objects.filter(upload_batch=latest)
                         .values_list("raw_data__rctdate", flat=True)), default="") if latest else ""
    file_info = {
        "preview": dry_run,
        "sheet": prepared["sheet"],
        "date_order": prepared["date_order"],
        "rows_in_file": len(prepared["rows"]),
        "rows_kept": len(kept_rows),
        "rows_left_out": sum(left_out.values()),
        "left_out_by_reason": {FILTER_REASONS[key]: count for key, count in left_out.items()},
        "date_problems": prepared["problems"][:MAX_REPORTED_PROBLEMS],
        "date_problems_count": len(prepared["problems"]),
        "older_than_latest": ({"file": file_newest, "latest": latest_newest}
                              if file_newest and latest_newest and file_newest < latest_newest else None),
    }

    try:
        with transaction.atomic(), history.source(f"TB-LIS upload: {source_filename}"):
            result = _merge_tblis_rows(self, kept_rows, prepared["columns"], user_id, source_filename, prepared["rows"])
            result["follow_up_count"] = _save_follow_up(prepared["rows"], result.get("upload_batch_id"))
            if dry_run:
                raise _PreviewRollback(result)
    except _PreviewRollback as preview:
        result = preview.result
        result.pop("upload_batch_id", None)

    result.update(file_info)
    return result


def _save_follow_up(rows, batch_id):
    """Replace the follow-up list with this upload's rows. Only what the page shows is kept."""
    TblisFollowUp.objects.all().delete()
    records = []
    for row, reason in follow_up_rows(rows):
        if row.get("labno"):
            records.append(TblisFollowUp(
                labno=row["labno"], reason=reason, upload_batch_id=batch_id,
                specimen=row.get("spectype", "")[:50], genexpert=row.get("peripheralres_genexpert", "")[:100],
                region=row.get("tbregion", "")[:100], facility=row.get("hfacility", "")[:200],
                received=row.get("rctdate", "")[:10],
                has_dst=any(row.get(col) for col in ("ljdst1_date", "ljdst2_date", "mgitdst1_date", "mgitdst2_date")),
            ))
    TblisFollowUp.objects.bulk_create(records, batch_size=1000)
    return len(records)


def _save_left_out(rows, upload_batch):
    """The lab numbers this file rejects. One it also has an accepted row for isn't rejected."""
    accepted, rejected = set(), {}
    for row in rows:
        reason = filter_reason(row)
        if not row.get("labno"):
            continue
        if reason:
            rejected.setdefault(row["labno"], reason)
        elif not is_isolate(row):
            accepted.add(row["labno"])
    records = [
        TblisLeftOut(labno=labno, reason=reason, upload_batch=upload_batch, seen_at=upload_batch.created_at)
        for labno, reason in rejected.items() if labno not in accepted
    ]
    TblisLeftOut.objects.bulk_create(records, batch_size=1000)


def _record_values(record):
    if record is None:
        return None
    skip = ("created_at", "updated_at")
    values = {field.attname: _plain(getattr(record, field.attname)) for field in record._meta.fields if field.name not in skip}
    for field in record._meta.many_to_many:
        values[field.name] = sorted(getattr(record, field.name).values_list("pk", flat=True))
    return values


def _merge_tblis_rows(task, rows, columns, user_id, source_filename, file_rows):
    total = len(rows)
    processed = 0
    row_errors = []
    created = 0
    updated = 0
    isolates_merged = 0
    isolates_unmatched = 0
    upload_batch = TblisUploadBatch.objects.create(
        source_file_name=source_filename,
        uploaded_by_id=user_id,
    )

    # Clear previous discrepancies for a fresh start per upload session
    TblisNotInEdcs.objects.all().delete()
    set_aside = set_aside_lab_numbers()  # Substudy 4 Zonal Lab forms in the Recycle Bin
    set_aside_rows = 0
    EdcsNotInTblis.objects.all().delete()
    EdcsTblisMismatch.objects.all().delete()
    _save_left_out(file_rows, upload_batch)
    merged_labs = set()

    for idx, clean_row in enumerate(rows, start=1):
        if task.request.called_directly is False and getattr(task.request, "revoke", False):
            return {"state": "REVOKED", "processed": processed}

        labno = clean_row.get("labno", "")
        if not labno:
            continue
        try:
            with transaction.atomic():  # one savepoint per row: a failing row doesn't break the rest

                # 1. Save to Raw Staging Table
                raw_entry = TblisRawData.objects.create(
                    labno=labno,
                    raw_data=clean_row,
                    uploaded_by_id=user_id,
                    upload_batch=upload_batch,
                )

                # Other zones' isolates match on the number CTRL entered, and give the DST only
                if is_isolate(clean_row):
                    z_lab = ZonalLaboratory.objects.exclude(LAB_NUMBER_ONLY_Q).filter(isolate_unique_lab_no=labno).first()
                    if z_lab:
                        merge_isolate_dst(z_lab, clean_row, raw_entry.pk)
                        merged_labs.add(z_lab.pk)
                        raw_entry.is_merged = True
                        raw_entry.save(update_fields=['is_merged'])
                        isolates_merged += 1
                    else:
                        TblisNotInEdcs.objects.create(labno=labno, raw_data=clean_row)
                        isolates_unmatched += 1
                    processed += 1
                    continue

                # 2. Find matching ZonalLaboratory record
                z_lab = ZonalLaboratory.objects.filter(unique_lab_no=labno).first()

                if not z_lab and labno in set_aside:
                    set_aside_rows += 1  # Substudy 4, set aside in the Recycle Bin: expected
                    continue

                if not z_lab:
                    # TBLIS row not in ZonalLaboratory
                    TblisNotInEdcs.objects.create(labno=labno, raw_data=clean_row)
                    row_errors.append(f"Row {idx}: labno {labno} not found in ZonalLaboratory records.")
                    continue

                # 3. Apply TBLIS values only to CTRL laboratory records.
                is_ctrl_lab = False
                for prefix in CTRL_PREFIXES:
                    if z_lab.screening.pid.startswith(prefix):
                        is_ctrl_lab = True
                        break

                if is_ctrl_lab:
                    # Apply TBLIS transformations on top of ZonalLaboratory data.
                    sync_zonal_laboratory_to_edcs(z_lab, clean_row)
                    merged_labs.add(z_lab.pk)
                    raw_entry.is_merged = True
                    raw_entry.save(update_fields=['is_merged'])
                    updated += 1
                else:
                    # Non-Zonal: just sync from ZonalLaboratory without TBLIS data
                    sync_zonal_laboratory_to_edcs(z_lab, None)

        except Exception as e:
            row_errors.append(f"Row {idx} (labno={labno}): {e}")

        processed += 1
        if processed % 100 == 0:
            task.update_state(state="PROGRESS", meta={"current": processed, "total": total})

    # 4. Every other record as the nightly sync would leave it: this file's rejections take
    #    effect now, and records not in this file keep their last result (tblis_status.py).
    found_by_screening = tblis_status.record_statuses(ZonalLaboratory.objects.all())
    results_removed = not_in_latest = 0
    for z_lab in ZonalLaboratory.objects.select_related("screening"):
        found = found_by_screening.get(z_lab.screening_id, tblis_status.NEVER_SEEN)
        not_in_latest += found.state == tblis_status.NOT_IN_LATEST
        try:
            with transaction.atomic():
                if z_lab.pk in merged_labs:
                    if not z_lab.screening.pid.startswith(tuple(CTRL_PREFIXES)):
                        sync_zonal_laboratory_to_edcs(z_lab, None)
                    continue
                rejected = found.state == tblis_status.REJECTED
                current = EdcsTblisZonal.objects.filter(screening=z_lab.screening).first() if rejected else None
                before = _record_values(current)
                sync_with_latest_tblis(z_lab)
                if before is not None and before != _record_values(EdcsTblisZonal.objects.get(pk=current.pk)):
                    results_removed += 1
        except Exception as e:
            logger.error(f"Error syncing Zonal Lab {z_lab.pk}: {e}")
            row_errors.append(f"Could not update the record with lab number {z_lab.unique_lab_no}: {e}")

    # 5. Find CTRL EDCS records not in the uploaded TBLIS file (rows left out by
    #    the filter are not uploaded, so their records are listed here too).
    uploaded_labnos = TblisRawData.objects.filter(
        upload_batch=upload_batch
    ).values_list('labno', flat=True)
    ctrl_edcs_qs = EdcsTblisZonal.objects.filter(get_ctrl_prefix_query())
    missing_edcs = ctrl_edcs_qs.exclude(unique_lab_no__in=uploaded_labnos)

    edcs_missing_objs = []
    for edcs_rec in missing_edcs:
        pid = edcs_rec.screening.pid if hasattr(edcs_rec, 'screening') and edcs_rec.screening else None
        edcs_missing_objs.append(
            EdcsNotInTblis(unique_lab_no=edcs_rec.unique_lab_no, pid=pid)
        )

    if edcs_missing_objs:
        EdcsNotInTblis.objects.bulk_create(edcs_missing_objs, batch_size=1000)

    # 6. Create Merge Summary for UI Dashboard
    edcs_not_in_tblis_count = EdcsNotInTblis.objects.count()
    tblis_not_in_edcs_count = TblisNotInEdcs.objects.count()
    mismatches_count = EdcsTblisMismatch.objects.count()
    total_edcs = EdcsTblisZonal.objects.count()

    # Extract date range from filename (e.g. CTRL-TBLIS-DFN-AllData-SAMPLES_01-01-2025-to-31-03-2026.csv)
    import re
    date_from, date_to = "", ""
    match = re.search(r'(\d{2}-\d{2}-\d{4})-to-(\d{2}-\d{2}-\d{4})', source_filename)
    if match:
        date_from = match.group(1)
        date_to = match.group(2)

    EdcsTblisMergeSummary.objects.create(
        total_columns=len(columns),
        total_edcs_records=total_edcs,
        total_tblis_rows=total,
        matched_records=updated,
        missing_records=0,
        edcs_not_in_tblis=edcs_not_in_tblis_count,
        tblis_not_in_edcs=tblis_not_in_edcs_count,
        tblis_date_from=date_from,
        tblis_date_to=date_to,
        total_mismatch_columns=0,
        total_mismatch_records=mismatches_count,
        mismatch_by_field={},
        uploaded_by_id=user_id,
        upload_batch=upload_batch,
    )

    return {
        "current": processed,
        "total": total,
        "created": created,
        "updated": updated,
        "isolates_merged": isolates_merged,
        "isolates_unmatched": isolates_unmatched,
        "results_removed": results_removed,
        "not_in_latest_count": not_in_latest,
        "errors": row_errors,
        "state": "SUCCESS",
        "upload_batch_id": upload_batch.id,
        "edcs_not_in_tblis_count": edcs_not_in_tblis_count,
        "tblis_not_in_edcs_count": tblis_not_in_edcs_count,
        "set_aside_substudy4_count": set_aside_rows,
        "mismatches_count": mismatches_count,
    }


@shared_task
def sync_zonal_laboratory_daily():
    """
    Runs daily to synchronize any manual updates made in ZonalLaboratory 
    to EdcsTblisZonal. It applies TBLIS transformations logic (from the latest raw data)
    for records that match Zonal prefixes.
    """
    zonal_labs = ZonalLaboratory.objects.all()
    
    updated_count = 0
    for z_lab in zonal_labs:
        try:
            with history.source("Nightly sync"):
                sync_with_latest_tblis(z_lab)
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Error daily syncing {z_lab.unique_lab_no}: {e}")
            
    return {"status": "SUCCESS", "updated": updated_count}
