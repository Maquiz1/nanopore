import csv
import logging
import os
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
from nanopore.models.discrepancies import TblisNotInEdcs, EdcsNotInTblis, EdcsTblisMismatch
from options.models import (
    SampleAppearance, YesNo, CultureMethod, MicroscopyType, CultureMicroscopyResults,
    LJCultureResult, MGITCultureResult, YesNoNA, PhenotypicDSTResults,
    XpertXDRResults, XpertXDRResultsTwo, XpertXDRResultsThree,
    FirstLineDrugs, SecondLineDrugs,
    MTBResultsLPA, RIFResultLPA, INHResultLPA, NanoporeResults,
    NanoporeSequencingResults, NanoporeSequencingDelayedReasons
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

phenotypic_results_map = {
    "Resistance Detected": 1, "Resistance Inferred": 1, "Resistant": 1,
    "Resistance not Detected": 2, "Sensitive": 2,
    "Indeterminate": 3, "Resistance Indeterminate": 3,
    "MTB Not Detected": 5,
}

xpert_xdr_results_map = {
    "Resistance Detected": 1, "Resistance Inferred": 1, "Resistant": 1,
    "Resistance not Detected": 2, "Sensitive": 2,
    "Indeterminate": 3, "Resistance Indeterminate": 3,
    "MTB Not Detected": 4,
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

CTRL_PREFIXES = [
    "DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16",
    "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19"
]

def get_ctrl_prefix_query():
    prefix_query = Q()
    for prefix in CTRL_PREFIXES:
        prefix_query |= Q(screening__pid__startswith=prefix)
    return prefix_query

# --- TRANSFORMATION LOGIC ---
def apply_tblis_transformations(edcs_zonal, clean_row, labno):
    """
    Applies all TBLIS specific mapping transformations directly to the EdcsTblisZonal object,
    overwriting fields where TBLIS data is present and logging mismatches.
    """
    def log_mismatch(field, old_val, new_val):
        if old_val and new_val and str(old_val).strip() != str(new_val).strip():
            pid = edcs_zonal.screening.pid if hasattr(edcs_zonal, 'screening') and edcs_zonal.screening else None
            EdcsTblisMismatch.objects.create(
                labno=labno, pid=pid, field_name=field, 
                edcs_value=str(old_val), tblis_value=str(new_val)
            )

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
    culture_val = 1 if lj_date else 2
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
    
    # Infer microscopy type (1 for ZN, 2 for FM)
    mic_type_val = None
    if zn_date or zn_res:
        mic_type_val = 1
    if fm_date or fm_res:
        mic_type_val = 2
        
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

    # Culture Method (1 for LJ, 2 for MGIT)
    mgit_entry = clean_row.get("mgit_entrydate")
    cm_val = None
    if mgit_entry: cm_val = 2
    if lj_date: cm_val = 1
    
    if cm_val:
        existing_cm = list(edcs_zonal.culture_method.values_list('id', flat=True))
        old_cm_str = str(existing_cm[0]) if existing_cm else ""
        log_mismatch("culture_method", old_cm_str, str(cm_val))
        edcs_zonal.culture_method.set([cm_val])

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
    lj_res_val = lj_results_map.get(lj_res_str) if lj_res_str else None
    
    # Override rule: if id_res is "Mycobacteria other than M.tuberculosis" or "Negative" (7)
    id_res_map = {"Mycobacteria other than M.tuberculosis": 7, "Negative": 7, "Mycobacteria tuberculosis complex": 8, "Not Applicable": 8, "Not done": 8, "Positive": 8, "Presumptive M.tuberculosis complex": 8, "See comment": 8}
    id_res_val = id_res_map.get(id_res) if id_res else None
    if id_res_val == 7:
        lj_res_val = 7
        
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
    mgit_res_val = mgit_results_map.get(mgit_res_str) if mgit_res_str else None
    if mgit_res_val:
        log_mismatch("mgit_results_id", edcs_zonal.mgit_results_id, mgit_res_val)
        edcs_zonal.mgit_results_id = mgit_res_val

    # Phenotypic DST Date
    mgitdst1_date = clean_row.get("mgitdst1_date")
    mgitdst2_date = clean_row.get("mgitdst2_date")
    pheno_date = mgitdst1_date or mgitdst2_date
    # if pheno_date:
    #     parsed_pheno_date = parse_date_field(pheno_date)
    #     log_mismatch("phenotypic_date_results", edcs_zonal.phenotypic_date_results, parsed_pheno_date)
    #     edcs_zonal.phenotypic_date_results = parsed_pheno_date

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
    
    # Xpert XDR
    gxxdr_date = clean_row.get("gxxdr_date")
    xpert_performed_val = None
    if gxxdr_date:
        xpert_performed_val = 1
        parsed_xpert_date = parse_date_field(gxxdr_date)
        log_mismatch("xpert_xdr_date_performed", edcs_zonal.xpert_xdr_date_performed, parsed_xpert_date)
        edcs_zonal.xpert_xdr_date_performed = parsed_xpert_date
    
    if xpert_performed_val:
        log_mismatch("xpert_xdr_performed_id", edcs_zonal.xpert_xdr_performed_id, xpert_performed_val)
        edcs_zonal.xpert_xdr_performed_id = xpert_performed_val

    def apply_xdr(edcs_field, tblis_col):
        tblis_str = clean_row.get(tblis_col)
        val = xpert_xdr_results_map.get(tblis_str) if tblis_str else None
        if val:
            existing = getattr(edcs_zonal, f"{edcs_field}_id", None)
            log_mismatch(edcs_field, existing, val)
            setattr(edcs_zonal, f"{edcs_field}_id", val)
            
    apply_xdr("xpert_xdr_isoniazid", "gxxdr_isoniazid")
    apply_xdr("xpert_xdr_fluoroquinolones", "gxxdr_flq")
    apply_xdr("xpert_xdr_amikacin", "gxxdr_amikacin")
    apply_xdr("xpert_xdr_kanamycin", "gxxdr_kanamycin")
    apply_xdr("xpert_xdr_capreomycin", "gxxdr_capreomycin")
    apply_xdr("xpert_xdr_ethionamide", "gxxdr_ethionamide")
    
    # First-line and Second-line LPA
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
        
    e_zonal.unique_lab_no = z_lab.unique_lab_no or f"SYNC-{z_lab.screening.pid}"
    
    # Copy all standard fields exactly as-is
    exclude_fields = ['id', 'screening', 'created_at', 'created_by', 'updated_at', 'updated_by']
    for field in ZonalLaboratory._meta.fields:
        if field.name not in exclude_fields:
            val = getattr(z_lab, field.name)
            setattr(e_zonal, field.name, val)
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


# --- CELERY TASKS ---
@shared_task(bind=True)
def process_raw_tblis_upload(self, filepath, user_id=None, source_filename=None):
    """
    Reads a raw TBLIS CSV in memory-safe chunks, saves to TblisRawData,
    and merges matching records into EdcsTblisZonal.
    """
    total = sum(1 for _ in open(filepath, errors='ignore')) - 1
    processed = 0
    row_errors = []
    created = 0
    updated = 0
    upload_batch = TblisUploadBatch.objects.create(
        source_file_name=source_filename or os.path.basename(filepath),
        uploaded_by_id=user_id,
    )
    
    # Clear previous discrepancies for a fresh start per upload session
    TblisNotInEdcs.objects.all().delete()
    EdcsNotInTblis.objects.all().delete()
    EdcsTblisMismatch.objects.all().delete()

    with open(filepath, newline='', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        # Strip column names
        reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]
        
        for idx, row in enumerate(reader, start=2):
            if self.request.called_directly is False and getattr(self.request, "revoke", False):
                return {"state": "REVOKED", "processed": processed}
            
            try:
                clean_row = {k.strip(): str(v).strip() if v else v for k, v in row.items() if k}
                labno = clean_row.get("labno", "")

                if not labno:
                    continue
                
                # 1. Save to Raw Staging Table
                raw_entry = TblisRawData.objects.create(
                    labno=labno,
                    raw_data=clean_row,
                    uploaded_by_id=user_id,
                    upload_batch=upload_batch,
                )

                # 2. Find matching ZonalLaboratory record
                z_lab = ZonalLaboratory.objects.filter(unique_lab_no=labno).first()

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
                self.update_state(state="PROGRESS", meta={"current": processed, "total": total})

    # 4. Sync all non-CTRL records from ZonalLaboratory without TBLIS transformations.
    non_ctrl_labs = ZonalLaboratory.objects.exclude(get_ctrl_prefix_query())
    for z_lab in non_ctrl_labs:
        try:
            sync_zonal_laboratory_to_edcs(z_lab, None)
        except Exception as e:
            logger.error(f"Error syncing non-zonal {z_lab.unique_lab_no}: {e}")

    # 5. Find CTRL EDCS records not in the uploaded TBLIS file.
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
    filename = source_filename or os.path.basename(filepath)
    date_from, date_to = "", ""
    match = re.search(r'(\d{2}-\d{2}-\d{4})-to-(\d{2}-\d{2}-\d{4})', filename)
    if match:
        date_from = match.group(1)
        date_to = match.group(2)

    EdcsTblisMergeSummary.objects.create(
        total_columns=len(reader.fieldnames) if hasattr(reader, 'fieldnames') and reader.fieldnames else 0,
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
        "errors": row_errors,
        "state": "SUCCESS",
        "upload_batch_id": upload_batch.id,
        "edcs_not_in_tblis_count": EdcsNotInTblis.objects.count(),
        "tblis_not_in_edcs_count": TblisNotInEdcs.objects.count(),
        "mismatches_count": EdcsTblisMismatch.objects.count(),
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
            # Apply the latest raw TBLIS transformation only to CTRL laboratory records.
            is_ctrl_lab = False
            for prefix in CTRL_PREFIXES:
                if z_lab.screening.pid.startswith(prefix):
                    is_ctrl_lab = True
                    break
                    
            clean_row = None
            if is_ctrl_lab:
                # Find the latest TBLIS raw data for this labno
                raw_entry = TblisRawData.objects.filter(labno=z_lab.unique_lab_no).order_by('-uploaded_at').first()
                if raw_entry:
                    clean_row = raw_entry.raw_data
                    
            sync_zonal_laboratory_to_edcs(z_lab, clean_row)
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Error daily syncing {z_lab.unique_lab_no}: {e}")
            
    return {"status": "SUCCESS", "updated": updated_count}
