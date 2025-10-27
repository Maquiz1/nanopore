from django.apps import apps
from utils.permissions import filter_queryset_by_user_role

def regimen_report_total(request):
    """
    Returns total Regimen Change issues count for navbar:
    - Counts RegimenChanges with missing required fields.
    """
    regimen_total = 0

    if not request.user.is_authenticated:
        return {"regimen_report_total": regimen_total}

    RegimenChanges = apps.get_model('nanopore', 'RegimenChanges')
    regimens = RegimenChanges.objects.all()
    regimens = filter_queryset_by_user_role(request.user, regimens, site_field="screening__site")

    # --- Required fields for completeness ---
    required_fields = [
        "date",         # Date regimen was changed
        "drug",         # Drug name involved
        "changes",      # Type of change (e.g., substitution, modification)
        "reason",       # Reason for change
    ]

    for r in regimens:
        for field in required_fields:
            value = getattr(r, field)
            if value in [None, ""]:  # missing or empty
                regimen_total += 1
                break  # Count each incomplete record only once

    return {"regimen_report_total": regimen_total}
