# reports/context_processors.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def enrollment_report_total(request):
    """
    Returns total enrollment issues count for navbar:
    - Counts enrollments with missing required fields
    """
    enrollment_total = 0

    if not request.user.is_authenticated:
        return {"enrollment_report_total": enrollment_total}

    Enrollment = apps.get_model('nanopore', 'Enrollment')
    enrollments = Enrollment.objects.all()
    enrollments = filter_queryset_by_user_role(request.user, enrollments, site_field="screening__site")

    # --- Required fields to check ---
    required_fields = [
        'enrollment_date', 'cough2weeks', 'poor_weight', 'coughing_blood',
        'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
        'date_information_collected', 'tx_previous'
    ]

    for e in enrollments:
        for field in required_fields:
            if not getattr(e, field):
                enrollment_total += 1
                break  # Count each enrollment only once

    return {"enrollment_report_total": enrollment_total}
