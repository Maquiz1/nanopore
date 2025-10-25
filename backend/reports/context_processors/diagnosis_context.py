# utils/context_processors.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def diagnosis_report_total(request):
    """
    Returns total diagnosis issues count for navbar:
    - Counts diagnoses with missing required fields
    """
    diagnosis_total = 0

    if not request.user.is_authenticated:
        return {"diagnosis_report_total": diagnosis_total}

    Diagnosis = apps.get_model('nanopore', 'Diagnosis')
    diagnoses = Diagnosis.objects.all()
    diagnoses = filter_queryset_by_user_role(request.user, diagnoses, site_field="screening__site")

    # --- Required fields to check ---
    required_fields = [
        'enrollment_date', 'cough2weeks', 'poor_weight', 'coughing_blood',
        'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
        'date_information_collected', 'tx_previous'
    ]

    for d in diagnoses:
        for field in required_fields:
            if not getattr(d, field):
                diagnosis_total += 1
                break  # Count each diagnosis only once

    return {"diagnosis_report_total": diagnosis_total}
