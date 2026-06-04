from .form_queries.screening_context import screening_report_total
from .form_queries.enrollment_context import enrollment_report_total
from .form_queries.regimen_context import regimen_report_total
from .form_queries.diagnosis_context import diagnosis_report_total
from .form_queries.clinic_laboratory_context import clinic_report_total
from .form_queries.edcs_tblis_laboratory_context_processor import edcs_tblis_report_total

def specific_queries_total(request):
    """
    Aggregates quality issue counts across all major forms exactly matching the UI visibility rules.
    """
    if not request.user.is_authenticated:
        return {'context_specific_queries_total': 0}

    user = request.user
    user_group = user.groups.first().name.upper() if user.groups.exists() else ""
    is_super = user.is_superuser

    show_clinical = is_super or user_group in ["ADMIN", "REVIEWER", "NURSE", "CLINICIAN"]
    show_edcs = is_super or user_group in ["ADMIN", "REVIEWER"]

    total = 0

    if show_clinical:
        total += screening_report_total(request).get('context_screening_report_total', 0)
        total += enrollment_report_total(request).get('context_enrollment_report_total', 0)
        total += regimen_report_total(request).get('context_regimen_report_total', 0)
        total += diagnosis_report_total(request).get('context_diagnosis_report_total', 0)
        total += clinic_report_total(request).get('context_clinic_report_total', 0)
    
    if show_edcs:
        total += edcs_tblis_report_total(request).get('context_edcs_tblis_report_total', 0)

    return {'context_specific_queries_total': total}