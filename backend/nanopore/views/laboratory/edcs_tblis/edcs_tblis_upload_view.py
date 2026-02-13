# nanopore/views/laboratory/edcs_tblis/edcs_tblis_upload_view.py


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


# nanopore/views.py

from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import default_storage
from nanopore.forms.laboratory.edcs_tblis.edcs_tblis_lab_upload_form import EdcsTBLISLabUploadForm
from nanopore.tasks import import_edcs_tblis


class EdcsTBLISCsvUploadView(View):
    template_name = "nanopore/laboratory/edcs_tblis/edcs_tblis_laboratory_upload.html"

    def get(self, request):
        return render(request, self.template_name, {"form": EdcsTBLISLabUploadForm()})

    def post(self, request):
        form = EdcsTBLISLabUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        file = request.FILES["file"]

        # save file to disk
        path = default_storage.save(f"imports/{file.name}", file)

        # launch background task
        task = import_edcs_tblis.delay(path)

        return JsonResponse({
            "task_id": task.id
        })
