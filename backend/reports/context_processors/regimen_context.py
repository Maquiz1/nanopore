# utils/context_processors.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def regimen_report_total(request):
    """
    Returns total regimen issues count for navbar:
    - Counts regimens with missing required fields
    """
    regimen_total = 0

    if not request.user.is_authenticated:
        return {"regimen_report_total": regimen_total}

    Regimen = apps.get_model('nanopore', 'RegimenChanges')
    regimens = Regimen.objects.all()
    regimens = filter_queryset_by_user_role(request.user, regimens, site_field="screening__site")

    # --- Required fields to check ---
    required_fields = [
        'enrollment_date', 'cough2weeks', 'poor_weight', 'coughing_blood',
        'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
        'date_information_collected', 'tx_previous'
    ]
    for r in regimens:
        for field in required_fields:
            if not getattr(r, field):
                regimen_total += 1
                break  # Count each regimen only once

    return {"regimen_report_total": regimen_total}
