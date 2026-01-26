# reports/context_processors.py
# ──────────────────────────────────────────────────────────────
# Central place to combine all form-specific quality issue counts
# ──────────────────────────────────────────────────────────────

from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

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
    Aggregates quality issue counts across all major forms for:
    - Dashboard overviews
    - Navbar badges
    - Data quality summary cards
    
    Returns a single integer total.
    """
    if not request.user.is_authenticated:
        return {'specific_queries_total': 0}

    total = 0

    # ── Screening ────────────────────────────────────────
    screening_data = screening_report_total(request)
    total += screening_data.get('screening_report_total', 0)

    # ── Enrollment ───────────────────────────────────────
    enrollment_data = enrollment_report_total(request)
    total += enrollment_data.get('enrollment_report_total', 0)

    # ── Regimen Changes ──────────────────────────────────
    regimen_data = regimen_report_total(request)
    total += regimen_data.get('regimen_report_total', 0)

    # ── Diagnosis ────────────────────────────────────────
    diagnosis_data = diagnosis_report_total(request)
    total += diagnosis_data.get('diagnosis_report_total', 0)

    # ── Clinic Laboratory ────────────────────────────────
    clinic_data = clinic_report_total(request)
    # Use the aggregated total if available, otherwise sum components
    total += clinic_data.get('clinic_report_total', 0)

    # ── Zonal Laboratory ─────────────────────────────────
    zonal_data = zonal_report_total(request)
    total += zonal_data.get('zonal_report_total', 0)

    return {'specific_queries_total': total}