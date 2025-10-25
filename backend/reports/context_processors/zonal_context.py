# utils/context_processors.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def zonal_report_total(request):
    """
    Returns total zonal issues count for navbar:
    - Counts zones with missing required fields
    """
    zonal_total = 0

    if not request.user.is_authenticated:
        return {"zonal_report_total": zonal_total}

    Zonal = apps.get_model('nanopore', 'ZonalLaboratory')
    zonals = Zonal.objects.all()
    zonals = filter_queryset_by_user_role(request.user, zonals, site_field="screening__site")

    # --- Required fields to check ---
    required_fields = [
        'enrollment_date', 'cough2weeks', 'poor_weight', 'coughing_blood',
        'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
        'date_information_collected', 'tx_previous'
    ]

    for z in zonals:
        for field in required_fields:
            if not getattr(z, field):
                zonal_total += 1
                break  # Count each zonal only once

    return {"zonal_report_total": zonal_total}
