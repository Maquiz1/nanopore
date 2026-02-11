import csv
import io
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError

from nanopore.forms.laboratory.zonal.zonal_lab_upload_form import ZonalLabUploadForm
from nanopore.forms.laboratory.edcs_tblis.edcs_tblis_lab_upload_form import EdcsTBLISLabUploadForm
from nanopore.models.zonal_lab import ZonalLaboratory
from nanopore.models.edcs_tblis_zonal import EdcsTblisZonal
from nanopore.models.screening import Screening
from options.models import (
    SampleAppearance, YesNo, CultureMethod, MicroscopyType, CultureMicroscopyResults,
    LJCultureResult, MGITCultureResult, YesNoNA, PhenotypicDSTResults,
    XpertXDRResults, XpertXDRResultsTwo, XpertXDRResultsThree,
    FirstLineDrugs, SecondLineDrugs,
    MTBResultsLPA, RIFResultLPA, INHResultLPA, NanoporeResults,NanoporeSequencingResults,NanoporeSequencingDelayedReasons
)

# --- helpers ---
def safe_int(val, required=False, field_name=None):
    """Convert to int if possible, else raise error if required."""
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required value for {field_name}")
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid integer value for {field_name}: {val}")


def safe_decimal(val, required=False, field_name=None):
    """Convert to float if possible, else raise error if required."""
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required value for {field_name}")
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid decimal value for {field_name}: {val}")


def parse_date_field(val, required=False, field_name=None):
    """Safely parse date string into YYYY-MM-DD, raise error if required."""
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required date for {field_name}")
        return None
    parsed = parse_date(str(val))
    if not parsed and required:
        raise ValidationError(f"Invalid date format for {field_name}: {val}")
    return parsed


def get_foreign(obj_class, val, required=False, field_name=None):
    """Safely get foreign key object by PK or by `value` field."""
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required foreign key for {field_name}")
        return None

    pk = safe_int(val)
    if hasattr(obj_class, "value"):
        obj = obj_class.objects.filter(value=pk).first()
    else:
        obj = obj_class.objects.filter(pk=pk).first()

    if required and not obj:
        raise ValidationError(f"Invalid foreign key for {field_name}: {val}")
    return obj


def split_m2m(obj_class, val, required=False, field_name=None):
    """Split comma-separated M2M values and return queryset list."""
    if not val or str(val).lower() in ["none", "nan", ""]:
        if required:
            raise ValidationError(f"Missing required M2M values for {field_name}")
        return []

    val = str(val).replace(";", ",")

    result = []
    for v in str(val).split(","):
        v = v.strip()
        if v:
            obj = get_foreign(obj_class, v, required=True, field_name=field_name)
            if obj:
                result.append(obj)
    return result



class EdcsTBLISCsvUploadView(View):
    template_name = "nanopore/laboratory/edcs_tblis/edcs_tblis_laboratory_upload.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"form": EdcsTBLISLabUploadForm()})

    def post(self, request, *args, **kwargs):
        form = EdcsTBLISLabUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        file = form.cleaned_data["file"]
        if not file.name.endswith(".csv"):
            messages.error(request, "Please upload a CSV file.")
            return render(request, self.template_name, {"form": form})

        data_set = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(data_set))

        count_created, count_updated, row_errors = 0, 0, []

        for idx, row in enumerate(reader, start=2):
            pid = row.get("pid") or row.get("pid")
            if not pid:
                row_errors.append(f"Row {idx}: Missing pid")
                continue

            try:
                screening = Screening.objects.filter(pid=pid).first()
                if not screening:
                    raise ValueError(f"No Screening found with pid={pid}")

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

                    "phenotypic_performed": get_foreign(YesNo, row.get("phenotypic_performed")),
                    "phenotypic_date_performed": parse_date_field(row.get("phenotypic_date_performed")),
                    "phenotypic_date_results": parse_date_field(row.get("phenotypic_date_results")),

                    # DST results
                    "rifampicin": get_foreign(PhenotypicDSTResults, row.get("rifampicin")),
                    "isoniazid": get_foreign(PhenotypicDSTResults, row.get("isoniazid")),
                    "levofloxacin": get_foreign(PhenotypicDSTResults, row.get("levofloxacin")),
                    "moxifloxacin": get_foreign(PhenotypicDSTResults, row.get("moxifloxacin")),
                    "bedaquiline": get_foreign(PhenotypicDSTResults, row.get("bedaquiline")),
                    "linezolid": get_foreign(PhenotypicDSTResults, row.get("linezolid")),
                    "clofazimine": get_foreign(PhenotypicDSTResults, row.get("clofazimine")),
                    "cycloserine": get_foreign(PhenotypicDSTResults, row.get("cycloserine")),
                    "terizidone": get_foreign(PhenotypicDSTResults, row.get("terizidone")),
                    "ethambutol": get_foreign(PhenotypicDSTResults, row.get("ethambutol")),
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

                lab, created = EdcsTblisZonal.objects.update_or_create(
                    screening=screening, defaults=defaults
                )

                # ManyToMany
                lab.culture_method.set(split_m2m(CultureMethod, row.get("culture_method")))
                lab.first_line_drugs.set(split_m2m(FirstLineDrugs, row.get("first_line_drugs")))
                lab.second_line_drugs.set(split_m2m(SecondLineDrugs, row.get("second_line_drugs")))
                lab.lpa1_inh.set(split_m2m(INHResultLPA, row.get("lpa1_inh")))
                lab.sequencing_delayed_reasons.set(split_m2m(NanoporeSequencingDelayedReasons, row.get("sequencing_delayed_reasons")))

                count_created += int(created)
                count_updated += int(not created)

            except Exception as e:
                row_errors.append(f"Row {idx} (pid={pid}): {e}")

        # --- Feedback ---
        if row_errors:
            messages.error(request, "Some rows had errors. Please fix them and re-upload.")
            return render(
                request,
                self.template_name,
                {"form": EdcsTBLISLabUploadForm(), "row_errors": row_errors,
                 "count_created": count_created, "count_updated": count_updated},
            )

        if count_created or count_updated:
            messages.success(request, f"Imported {count_created} new and updated {count_updated} records.")
        return redirect("nanopore:edcs-tblis-laboratory-list")
