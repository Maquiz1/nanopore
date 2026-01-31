# reports/context_processors.py
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

# Import all individual report total functions
# Adjust file names / module paths according to your actual structure
from .screening_context import screening_report_total
from .enrollment_context import enrollment_report_total
from .regimen_context   import regimen_report_total     # assuming you moved it to regimen_context.py
from .diagnosis_context import diagnosis_report_total   # assuming separate file
from .clinic_laboratory_context    import clinic_report_total      # assuming separate file
from .zonal_laboratory_context import zonal_report_total       # assuming separate file


def specific_queries_total(request):
    """
    Aggregates quality issue counts across all major forms with role-aware visibility.
    
    Returns only {'specific_queries_total': total}
    """
    if not request.user.is_authenticated:
        return {'specific_queries_total': 0}

    # Role context
    role_context = get_role_context(request.user)
    is_zonal_lab = role_context.get("is_zonal_lab", False)
    is_admin     = role_context.get("is_admin", False)
    is_reviewer  = role_context.get("is_reviewer", False)
    is_superuser = request.user.is_superuser
    is_full_access = is_admin or is_superuser
    is_privileged = is_admin or is_reviewer

    # Get individual report totals (these functions should already be role-aware)
    screening_total  = screening_report_total(request).get('screening_report_total', 0)
    enrollment_total = enrollment_report_total(request).get('enrollment_report_total', 0)
    regimen_total    = regimen_report_total(request).get('regimen_report_total', 0)
    diagnosis_total  = diagnosis_report_total(request).get('diagnosis_report_total', 0)
    clinic_total     = clinic_report_total(request).get('clinic_report_total', 0)
    zonal_total      = zonal_report_total(request).get('zonal_report_total', 0)

    # Compute total based on role
    if is_privileged:
        # Admins / Reviewers see everything
        total = (
            screening_total +
            enrollment_total +
            regimen_total +
            diagnosis_total +
            clinic_total +
            zonal_total
        )
    elif is_zonal_lab:
        # Zonal lab users only see zonal issues
        total = zonal_total
    else:
        # Normal users see everything except zonal
        total = (
            screening_total +
            enrollment_total +
            regimen_total +
            diagnosis_total +
            clinic_total
        )

    return {'specific_queries_total': total}