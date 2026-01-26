from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def diagnosis_report_total(request):
    """
    Returns total diagnosis issues count for navbar:
    - Counts Diagnosis records with missing required fields
    """
    diagnosis_total = 0

    if not request.user.is_authenticated:
        return {"diagnosis_report_total": diagnosis_total}

    Diagnosis = apps.get_model('nanopore', 'Diagnosis')
    diagnoses = Diagnosis.objects.all()
    diagnoses = filter_queryset_by_user_role(request.user, diagnoses, site_field="screening__site")

    # # --- Required fields to check ---
    required_fields = [
        "tb_diagnosis",
    #     "tb_diagnosis_date",
    #     "tb_diagnosis_made",
    #     "bacteriological_diagnosis",
    #     "tb_treatment",
    #     "tb_treatment_date",
    #     "tb_facility",
    #     "tb_regimen",
    #     "tb_outcome2",
    ]

    for d in diagnoses:
        for field in required_fields:
            value = getattr(d, field)
            if value in [None, "", False]:
                diagnosis_total += 1
                break  # Count each diagnosis only once

    return {"diagnosis_report_total": diagnosis_total}
