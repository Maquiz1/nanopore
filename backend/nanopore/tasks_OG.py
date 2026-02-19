# nanopore/tasks.py
from celery import shared_task
import csv
from django.apps import apps
from django.core.exceptions import ValidationError

from nanopore.views.laboratory.edcs_tblis.edcs_tblis_upload_view import (
    safe_int, safe_decimal, parse_date_field,
    get_foreign, split_m2m
)

from options.models import (
    SampleAppearance, YesNo, CultureMethod, MicroscopyType, CultureMicroscopyResults,
    LJCultureResult, MGITCultureResult, YesNoNA, PhenotypicDSTResults,
    XpertXDRResults, XpertXDRResultsTwo, XpertXDRResultsThree,
    FirstLineDrugs, SecondLineDrugs,
    MTBResultsLPA, RIFResultLPA, INHResultLPA, NanoporeResults,
    NanoporeSequencingResults, NanoporeSequencingDelayedReasons
)


@shared_task(bind=True)
def import_edcs_tblis(self, filepath):

    Screening = apps.get_model("nanopore", "Screening")
    EdcsTblisZonal = apps.get_model("nanopore", "EdcsTblisZonal")

    total = sum(1 for _ in open(filepath)) - 1
    processed = 0

    row_errors = []
    created = 0
    updated = 0

    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=2):

            # --- Check if task was revoked ---
            if self.request.called_directly is False and self.is_revoked():
                # Stop processing immediately
                return {
                    "current": processed,
                    "total": total,
                    "created": created,
                    "updated": updated,
                    "errors": row_errors,
                    "state": "REVOKED"
                }

            pid = row.get("pid")

            try:
                screening = Screening.objects.filter(pid=pid).first()
                if not screening:
                    raise ValidationError(f"No Screening found pid={pid}")

                # --- build defaults dict and set M2M fields ---
                defaults = {
                    "date_sputum_received": parse_date_field(row.get("date_sputum_received")),
                    "appearance": get_foreign(SampleAppearance, row.get("appearance")),
                    "sample_volume": safe_decimal(row.get("sample_volume")),
                    "unique_lab_no": row.get("unique_lab_no") or None,

                    "culture_performed": get_foreign(YesNo, row.get("culture_performed")),
                    "microscopy_type": get_foreign(MicroscopyType, row.get("microscopy_type")),
                    "microscopy_date": parse_date_field(row.get("microscopy_date")),
                    "microscopy_results": get_foreign(CultureMicroscopyResults, row.get("microscopy_results")),

                    "lj_inoculation_date": parse_date_field(row.get("lj_inoculation_date")),
                    "lj_results_date": parse_date_field(row.get("lj_results_date")),
                    "lj_results": get_foreign(LJCultureResult, row.get("lj_results")),

                    "mgit_inoculation_date": parse_date_field(row.get("mgit_inoculation_date")),
                    "mgit_results_date": parse_date_field(row.get("mgit_results_date")),
                    "mgit_results": get_foreign(MGITCultureResult, row.get("mgit_results")),

                    "culture_isolate": get_foreign(YesNoNA, row.get("culture_isolate")),
                    "isolate_date": parse_date_field(row.get("isolate_date")),
                    "isolate_unique_lab_no": row.get("unique_lab_no") or None,

                    "phenotypic_performed": get_foreign(YesNo, row.get("phenotypic_performed")),
                    # "phenotypic_date_performed": parse_date_field(row.get("phenotypic_date_performed")),
                    # "phenotypic_date_results": parse_date_field(row.get("phenotypic_date_results")),
                    "first_line_dst_performed": get_foreign(YesNo, row.get("first_line_dst_performed")),
                    "first_line_dst_performed_date": parse_date_field(row.get("first_line_dst_performed_date")),
                    "first_line_dst_results_date": parse_date_field(row.get("first_line_dst_results_date")),
                    
                    "second_line_dst_performed": get_foreign(YesNo, row.get("second_line_dst_performed")),
                    "second_line_dst_performed_date": parse_date_field(row.get("second_line_dst_performed_date")),
                    "second_line_dst_results_date": parse_date_field(row.get("second_line_dst_results_date")),

                    # DST results
                    "rifampicin": get_foreign(PhenotypicDSTResults, row.get("rifampicin")),
                    "isoniazid": get_foreign(PhenotypicDSTResults, row.get("isoniazid")),
                    "ethambutol": get_foreign(PhenotypicDSTResults, row.get("ethambutol")),
 
                    "levofloxacin": get_foreign(PhenotypicDSTResults, row.get("levofloxacin")),
                    "moxifloxacin": get_foreign(PhenotypicDSTResults, row.get("moxifloxacin")),
                    "bedaquiline": get_foreign(PhenotypicDSTResults, row.get("bedaquiline")),
                    "linezolid": get_foreign(PhenotypicDSTResults, row.get("linezolid")),
                    "clofazimine": get_foreign(PhenotypicDSTResults, row.get("clofazimine")),
                    "pretomanid": get_foreign(PhenotypicDSTResults, row.get("pretomanid")),
                    
                    "cycloserine": get_foreign(PhenotypicDSTResults, row.get("cycloserine")),
                    "terizidone": get_foreign(PhenotypicDSTResults, row.get("terizidone")),
                    "delamanid": get_foreign(PhenotypicDSTResults, row.get("delamanid")),
                    "pyrazinamide": get_foreign(PhenotypicDSTResults, row.get("pyrazinamide")),
                    "imipenem": get_foreign(PhenotypicDSTResults, row.get("imipenem")),
                    "cilastatin": get_foreign(PhenotypicDSTResults, row.get("cilastatin")),
                    "meropenem": get_foreign(PhenotypicDSTResults, row.get("meropenem")),
                    "amikacin": get_foreign(PhenotypicDSTResults, row.get("amikacin")),
                    "streptomycin": get_foreign(PhenotypicDSTResults, row.get("streptomycin")),
                    "ethionamide": get_foreign(PhenotypicDSTResults, row.get("ethionamide")),
                    "prothionamide": get_foreign(PhenotypicDSTResults, row.get("prothionamide")),
                    "para_aminosalicylic_acid": get_foreign(PhenotypicDSTResults, row.get("para_aminosalicylic_acid")),

                    # Xpert XDR
                    "xpert_xdr_performed": get_foreign(YesNo, row.get("xpert_xdr_performed")),
                    "xpert_xdr_date_performed": parse_date_field(row.get("xpert_xdr_date_performed")),
                    "xpert_xdr_isoniazid": get_foreign(XpertXDRResults, row.get("xpert_xdr_isoniazid")),
                    "xpert_xdr_fluoroquinolones": get_foreign(XpertXDRResults, row.get("xpert_xdr_fluoroquinolones")),
                    "xpert_xdr_amikacin": get_foreign(XpertXDRResultsThree, row.get("xpert_xdr_amikacin")),
                    "xpert_xdr_kanamycin": get_foreign(XpertXDRResultsThree, row.get("xpert_xdr_kanamycin")),
                    "xpert_xdr_capreomycin": get_foreign(XpertXDRResultsThree, row.get("xpert_xdr_capreomycin")),
                    "xpert_xdr_ethionamide": get_foreign(XpertXDRResultsTwo, row.get("xpert_xdr_ethionamide")),

                    # LPA
                    "lpa": get_foreign(YesNo,row.get("lpa")),
                    "first_line_lpa": get_foreign(YesNo, row.get("first_line_lpa")),
                    "first_line_lpa_date": parse_date_field(row.get("first_line_lpa_date")),
                    "lpa1_mtb": get_foreign(MTBResultsLPA, row.get("lpa1_mtb")),
                    "lpa1_rif": get_foreign(RIFResultLPA, row.get("lpa1_rif")),
                    # "lpa1_inh": get_foreign(INHResultLPA, row.get("LPA1INH")),
                    "second_line_lpa": get_foreign(YesNo, row.get("second_line_lpa")),
                    "second_line_lpa_date": parse_date_field(row.get("second_line_lpa_date")),
                    "lpa2_mtb": get_foreign(MTBResultsLPA, row.get("lpa2_mtb")),
                    "lpa2_rfluoroquinolones": get_foreign(RIFResultLPA, row.get("lpa2_rfluoroquinolones")),
                    "lpa2_aminoglycosides": get_foreign(RIFResultLPA, row.get("lpa2_aminoglycosides")),
                    "lpa2_kanamycin": get_foreign(RIFResultLPA, row.get("lpa2_kanamycin")),

                    # Nanopore
                    "nanopore_done": get_foreign(YesNo, row.get("nanopore_done")),
                    "nanopore_sequencing_date": parse_date_field(row.get("nanopore_sequencing_date")),
                    "nanopore_results": get_foreign(NanoporeSequencingResults, row.get("nanopore_results")),

                    # EPI TO ME
                    "epi_to_me": get_foreign(YesNo, row.get("epi_to_me")),
                    "epi_to_me_version": row.get("epi_to_me_version") or None,
                    "epi_to_me_date": parse_date_field(row.get("epi_to_me_date")),
                    "sequencing_results": get_foreign(YesNo, row.get("sequencing_results")),
                    
                    # delay
                    "sequencing_delayed": get_foreign(YesNo, row.get("sequencing_delayed")),
                    # "sequencing_delayed_days": row.get("sequencing_delayed_days") or None,
                    "sequencing_delayed_days": safe_int(row.get("sequencing_delayed_days")),
                    "sequencing_delayed_others": row.get("sequencing_delayed_others") or None,
                    
                    # NANOPORE RESULTS                  
                    "nano_amikacin": get_foreign(NanoporeResults, row.get("nano_amikacin")),
                    "nano_bedaquiline": get_foreign(NanoporeResults, row.get("nano_bedaquiline")),
                    "nano_capreomycin": get_foreign(NanoporeResults, row.get("nano_capreomycin")),
                    "nano_clofazimine": get_foreign(NanoporeResults, row.get("nano_clofazimine")),
                    "nano_delamanid": get_foreign(NanoporeResults, row.get("nano_delamanid")),
                    "nano_ethambutol": get_foreign(NanoporeResults, row.get("nano_ethambutol")),
                    "nano_ethionamide": get_foreign(NanoporeResults, row.get("nano_ethionamide")),
                    "nano_isoniazid": get_foreign(NanoporeResults, row.get("nano_isoniazid")),
                    "nano_kanamycin": get_foreign(NanoporeResults, row.get("nano_kanamycin")),
                    "nano_levofloxacin": get_foreign(NanoporeResults, row.get("nano_levofloxacin")),
                    "nano_linezolid": get_foreign(NanoporeResults, row.get("nano_linezolid")),
                    "nano_moxifloxacin": get_foreign(NanoporeResults, row.get("nano_moxifloxacin")),
                    "nano_pretomanid": get_foreign(NanoporeResults, row.get("nano_pretomanid")),
                    "nano_pyrazinamide": get_foreign(NanoporeResults, row.get("nano_pyrazinamide")),
                    "nano_rifampicin": get_foreign(NanoporeResults, row.get("nano_rifampicin")),
                    "nano_streptomycin": get_foreign(NanoporeResults, row.get("nano_streptomycin")),

                    "remarks": row.get("remarks") or None,
                }

                # lab, was_created = EdcsTblisZonal.objects.update_or_create(
                #     screening=screening,
                #     defaults=defaults
                # )

                # lab.culture_method.set(split_m2m(CultureMethod, row.get("culture_method")))
                # lab.first_line_drugs.set(split_m2m(FirstLineDrugs, row.get("first_line_drugs")))
                # lab.second_line_drugs.set(split_m2m(SecondLineDrugs, row.get("second_line_drugs")))
                # lab.lpa1_inh.set(split_m2m(INHResultLPA, row.get("lpa1_inh")))
                # lab.sequencing_delayed_reasons.set(
                #     split_m2m(NanoporeSequencingDelayedReasons, row.get("sequencing_delayed_reasons"))
                # )

                lab, was_created = EdcsTblisZonal.objects.update_or_create(
                    screening=screening,
                    defaults=defaults
                )

                lab.culture_method.set(split_m2m(CultureMethod, row.get("culture_method")))
                lab.first_line_drugs.set(split_m2m(FirstLineDrugs, row.get("first_line_drugs")))
                lab.second_line_drugs.set(split_m2m(SecondLineDrugs, row.get("second_line_drugs")))
                lab.lpa1_inh.set(split_m2m(INHResultLPA, row.get("lpa1_inh")))
                lab.sequencing_delayed_reasons.set(
                    split_m2m(NanoporeSequencingDelayedReasons, row.get("sequencing_delayed_reasons"))
                )

                created += int(was_created)
                updated += int(not was_created)

            except Exception as e:
                row_errors.append(f"Row {idx} (pid={pid}): {e}")

            processed += 1

            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={"current": processed, "total": total}
            )

    return {
        "current": processed,
        "total": total,
        "created": created,
        "updated": updated,
        "errors": row_errors,
        "state": "SUCCESS",
    }