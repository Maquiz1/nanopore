import csv
import io
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date

from nanopore.forms.laboratory.zonal.zonal_lab_upload_form import ZonalLabUploadForm
from nanopore.models.zonal_lab import ZonalLaboratory
from nanopore.models.screening import Screening
from options.models import (
    SampleAppearance, YesNo, CultureMethod, MicroscopyType, CultureMicroscopyResults,
    LJCultureResult, MGITCultureResult, YesNoNA, PhenotypicDSTResults,
    XpertXDRResults, XpertXDRResultsTwo, XpertXDRResultsThree,
    FirstLineDrugs, SecondLineDrugs,
    MTBResultsLPA, RIFResultLPA, INHResultLPA, NanoporeResults
)

# --- helpers ---
def safe_int(val):
    """Convert to int if possible, else None."""
    if val in [None, "", "None", "nan", "NaN"]:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def safe_decimal(val):
    """Convert to float if possible, else None."""
    if val in [None, "", "None", "nan", "NaN"]:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def parse_date_field(val):
    """Safely parse date string into YYYY-MM-DD."""
    if val in [None, "", "None", "nan", "NaN"]:
        return None
    parsed = parse_date(str(val))
    return parsed if parsed else None

def get_foreign(obj_class, val):
    """Safely get ForeignKey by ID or name."""
    if val in [None, "", "None", "nan", "NaN"]:
        return None
    pk = safe_int(val)
    if pk:
        return obj_class.objects.filter(pk=pk).first()
    return obj_class.objects.filter(name__iexact=str(val).strip()).first()

def split_m2m(obj_class, val):
    """Split M2M values like '1;2;3' and return queryset list."""
    if not val or str(val).lower() in ["none", "nan"]:
        return []
    result = []
    for v in str(val).split(";"):
        v = v.strip()
        if v:
            obj = get_foreign(obj_class, v)
            if obj:
                result.append(obj)
    return result


class ZonalLabCsvUploadView(View):
    template_name = "nanopore/laboratory/zonal/zonal_laboratory_upload.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"form": ZonalLabUploadForm()})

    def post(self, request, *args, **kwargs):
        form = ZonalLabUploadForm(request.POST, request.FILES)
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
            pid = row.get("PID") or row.get("pid")
            if not pid:
                row_errors.append(f"Row {idx}: Missing PID")
                continue

            try:
                screening = Screening.objects.filter(pid=pid).first()
                if not screening:
                    raise ValueError(f"No Screening found with PID={pid}")

                defaults = {
                    "date_sputum_received": parse_date_field(row.get("DateSputumReceived")),
                    "appearance": get_foreign(SampleAppearance, row.get("Appearance")),
                    "sample_volume": safe_decimal(row.get("SampleVolume")),
                    "unique_lab_no": row.get("UniqueLabNo") or None,

                    "culture_performed": get_foreign(YesNo, row.get("CulturePerformed")),
                    "microscopy_type": get_foreign(MicroscopyType, row.get("MicroscopyType")),
                    "microscopy_date": parse_date_field(row.get("MicroscopyDate")),
                    "microscopy_results": get_foreign(CultureMicroscopyResults, row.get("MicroscopyResults")),

                    "lj_inoculation_date": parse_date_field(row.get("LJInoculationDate")),
                    "lj_results_date": parse_date_field(row.get("LJResultsDate")),
                    "lj_results": get_foreign(LJCultureResult, row.get("LJResults")),

                    "mgit_inoculation_date": parse_date_field(row.get("MGITInoculationDate")),
                    "mgit_results_date": parse_date_field(row.get("MGITResultsDate")),
                    "mgit_results": get_foreign(MGITCultureResult, row.get("MGITResults")),

                    "culture_isolate": get_foreign(YesNoNA, row.get("CultureIsolate")),
                    "isolate_date": parse_date_field(row.get("IsolateDate")),

                    "phenotypic_performed": get_foreign(YesNo, row.get("PhenotypicPerformed")),
                    "phenotypic_date_performed": parse_date_field(row.get("PhenotypicDatePerformed")),
                    "phenotypic_date_results": parse_date_field(row.get("PhenotypicDateResults")),

                    # DST results
                    "rifampicin": get_foreign(PhenotypicDSTResults, row.get("Rifampicin")),
                    "isoniazid": get_foreign(PhenotypicDSTResults, row.get("Isoniazid")),
                    "levofloxacin": get_foreign(PhenotypicDSTResults, row.get("Levofloxacin")),
                    "moxifloxacin": get_foreign(PhenotypicDSTResults, row.get("Moxifloxacin")),
                    "bedaquiline": get_foreign(PhenotypicDSTResults, row.get("Bedaquiline")),
                    "linezolid": get_foreign(PhenotypicDSTResults, row.get("Linezolid")),
                    "clofazimine": get_foreign(PhenotypicDSTResults, row.get("Clofazimine")),
                    "cycloserine": get_foreign(PhenotypicDSTResults, row.get("Cycloserine")),
                    "terizidone": get_foreign(PhenotypicDSTResults, row.get("Terizidone")),
                    "ethambutol": get_foreign(PhenotypicDSTResults, row.get("Ethambutol")),
                    "delamanid": get_foreign(PhenotypicDSTResults, row.get("Delamanid")),
                    "pyrazinamide": get_foreign(PhenotypicDSTResults, row.get("Pyrazinamide")),
                    "imipenem": get_foreign(PhenotypicDSTResults, row.get("Imipenem")),
                    "cilastatin": get_foreign(PhenotypicDSTResults, row.get("Cilastatin")),
                    "meropenem": get_foreign(PhenotypicDSTResults, row.get("Meropenem")),
                    "amikacin": get_foreign(PhenotypicDSTResults, row.get("Amikacin")),
                    "streptomycin": get_foreign(PhenotypicDSTResults, row.get("Streptomycin")),
                    "ethionamide": get_foreign(PhenotypicDSTResults, row.get("Ethionamide")),
                    "prothionamide": get_foreign(PhenotypicDSTResults, row.get("Prothionamide")),
                    "para_aminosalicylic_acid": get_foreign(PhenotypicDSTResults, row.get("ParaAminosalicylicAcid")),

                    # Xpert XDR
                    "xpert_xdr_performed": get_foreign(YesNo, row.get("XpertXDRPerformed")),
                    "xpert_xdr_date_performed": parse_date_field(row.get("XpertXDRDatePerformed")),
                    "xpert_xdr_isoniazid": get_foreign(XpertXDRResults, row.get("XpertXDRIsoniazid")),
                    "xpert_xdr_fluoroquinolones": get_foreign(XpertXDRResults, row.get("XpertXDRFluoroquinolones")),
                    "xpert_xdr_amikacin": get_foreign(XpertXDRResultsThree, row.get("XpertXDRAmiKacin")),
                    "xpert_xdr_kanamycin": get_foreign(XpertXDRResultsThree, row.get("XpertXDRKanamycin")),
                    "xpert_xdr_capreomycin": get_foreign(XpertXDRResultsThree, row.get("XpertXDRCapreomycin")),
                    "xpert_xdr_ethionamide": get_foreign(XpertXDRResultsTwo, row.get("XpertXDREthionamide")),

                    # LPA
                    "first_line_lpa": get_foreign(YesNo, row.get("FirstLineLPA")),
                    "first_line_lpa_date": parse_date_field(row.get("FirstLineLPADate")),
                    "lpa1_mtb": get_foreign(MTBResultsLPA, row.get("LPA1MTB")),
                    "lpa1_rif": get_foreign(RIFResultLPA, row.get("LPA1RIF")),
                    # "lpa1_inh": get_foreign(INHResultLPA, row.get("LPA1INH")),
                    "second_line_lpa": get_foreign(YesNo, row.get("SecondLineLPA")),
                    "second_line_lpa_date": parse_date_field(row.get("SecondLineLPADate")),
                    "lpa2_mtb": get_foreign(MTBResultsLPA, row.get("LPA2MTB")),
                    "lpa2_rfluoroquinolones": get_foreign(RIFResultLPA, row.get("LPA2RFluoroquinolones")),
                    "lpa2_aminoglycosides": get_foreign(RIFResultLPA, row.get("LPA2Aminoglycosides")),
                    "lpa2_kanamycin": get_foreign(RIFResultLPA, row.get("LPA2Kanamycin")),

                    # Nanopore
                    "nanopore_done": get_foreign(YesNo, row.get("NanoporeDone")),
                    "sequencing_results": get_foreign(YesNo, row.get("SequencingResults")),
                    "epi_to_me": get_foreign(YesNo, row.get("EpiToMe")),
                    "epi_to_me_version": row.get("EpiToMeVersion") or None,
                    "nano_amikacin": get_foreign(NanoporeResults, row.get("NanoAmikacin")),
                    "nano_bedaquiline": get_foreign(NanoporeResults, row.get("NanoBedaquiline")),
                    "nano_capreomycin": get_foreign(NanoporeResults, row.get("NanoCapreomycin")),
                    "nano_clofazimine": get_foreign(NanoporeResults, row.get("NanoClofazimine")),
                    "nano_delamanid": get_foreign(NanoporeResults, row.get("NanoDelamanid")),
                    "nano_ethambutol": get_foreign(NanoporeResults, row.get("NanoEthambutol")),
                    "nano_ethionamide": get_foreign(NanoporeResults, row.get("NanoEthionamide")),
                    "nano_isoniazid": get_foreign(NanoporeResults, row.get("NanoIsoniazid")),
                    "nano_kanamycin": get_foreign(NanoporeResults, row.get("NanoKanamycin")),
                    "nano_levofloxacin": get_foreign(NanoporeResults, row.get("NanoLevofloxacin")),
                    "nano_linezolid": get_foreign(NanoporeResults, row.get("NanoLinezolid")),
                    "nano_moxifloxacin": get_foreign(NanoporeResults, row.get("NanoMoxifloxacin")),
                    "nano_pretomanid": get_foreign(NanoporeResults, row.get("NanoPretomanid")),
                    "nano_pyrazinamide": get_foreign(NanoporeResults, row.get("NanoPyrazinamide")),
                    "nano_rifampicin": get_foreign(NanoporeResults, row.get("NanoRifampicin")),
                    "nano_streptomycin": get_foreign(NanoporeResults, row.get("NanoStreptomycin")),

                    "remarks": row.get("Remarks") or None,
                }

                lab, created = ZonalLaboratory.objects.update_or_create(
                    screening=screening, defaults=defaults
                )

                # ManyToMany
                lab.culture_method.set(split_m2m(CultureMethod, row.get("CultureMethod")))
                lab.first_line_drugs.set(split_m2m(FirstLineDrugs, row.get("FirstLineDrugs")))
                lab.second_line_drugs.set(split_m2m(SecondLineDrugs, row.get("SecondLineDrugs")))
                lab.lpa1_inh.set(split_m2m(INHResultLPA, row.get("LPA1INH")))

                count_created += int(created)
                count_updated += int(not created)

            except Exception as e:
                row_errors.append(f"Row {idx} (PID={pid}): {e}")

        # --- Feedback ---
        if row_errors:
            messages.error(request, "Some rows had errors. Please fix them and re-upload.")
            return render(
                request,
                self.template_name,
                {"form": ZonalLabUploadForm(), "row_errors": row_errors,
                 "count_created": count_created, "count_updated": count_updated},
            )

        if count_created or count_updated:
            messages.success(request, f"Imported {count_created} new and updated {count_updated} records.")
        return redirect("nanopore:form-status-list")
