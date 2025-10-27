from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def clinic_report_total(request):
    """
    Returns total clinic issues count for navbar:
    - Counts ClinicLaboratory records with missing required fields
    """
    clinic_total = 0

    if not request.user.is_authenticated:
        return {"clinic_report_total": clinic_total}

    Clinic = apps.get_model('nanopore', 'ClinicLaboratory')
    clinics = Clinic.objects.all()
    clinics = filter_queryset_by_user_role(request.user, clinics, site_field="screening__site")

    # --- Required fields to check ---
    required_fields = [
        "sample_received",
        "number_received",
        "afb_microscopy_conducted",
        "xpert_mtb_rif_conducted",
        "date_sample1_collected",
        "date_sample1_received",
        "appearance_sample1",
        "afb_a_date",
        "technique_a",
        "afb_a_results",
        "xpert_date",
        "xpert_mtb",
        "xpert_rif",
    ]

    for c in clinics:
        for field in required_fields:
            value = getattr(c, field)
            if value in [None, "", False]:
                clinic_total += 1
                break  # Count each clinic only once

    return {"clinic_report_total": clinic_total}
