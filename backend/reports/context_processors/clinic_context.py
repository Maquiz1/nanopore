# utils/context_processors.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def clinic_report_total(request):
    """
    Returns total clinic issues count for navbar:
    - Counts clinics with missing required fields
    """
    clinic_total = 0

    if not request.user.is_authenticated:
        return {"clinic_report_total": clinic_total}

    Clinic = apps.get_model('nanopore', 'ClinicLaboratory')
    clinics = Clinic.objects.all()
    clinics = filter_queryset_by_user_role(request.user, clinics, site_field="screening__site")

    # --- Required fields to check ---
    required_fields = [
        'enrollment_date', 'cough2weeks', 'poor_weight', 'coughing_blood',
        'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
        'date_information_collected', 'tx_previous'
    ]


    for c in clinics:
        for field in required_fields:
            if not getattr(c, field):
                clinic_total += 1
                break  # Count each clinic only once

    return {"clinic_report_total": clinic_total}
