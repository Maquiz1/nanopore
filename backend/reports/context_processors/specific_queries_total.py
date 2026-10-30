from .form_queries.screening_context import screening_report_total
from .form_queries.enrollment_context import enrollment_report_total
from .form_queries.regimen_context import regimen_report_total
from .form_queries.diagnosis_context import diagnosis_report_total
from .form_queries.clinic_laboratory_context import clinic_report_total
from .form_queries.edcs_tblis_laboratory_context_processor import edcs_tblis_report_total
from .form_queries.zonal_laboratory_context import zonal_report_total
from utils import access
from utils.access import can_see_queries

def specific_queries_total(request):
    """
    Aggregates quality issue counts across all major forms exactly matching the UI visibility rules.
    """
    if not request.user.is_authenticated:
        return {'context_specific_queries_total': 0}

    # One entry per form: (form it belongs to, context processor, key it returns).
    # A form's queries count only if the user may work on them (utils/access.py).
    sources = [
        (access.SCREENING, screening_report_total, 'context_screening_report_total'),
        (access.ENROLLMENT, enrollment_report_total, 'context_enrollment_report_total'),
        (access.REGIMEN, regimen_report_total, 'context_regimen_report_total'),
        (access.DIAGNOSIS, diagnosis_report_total, 'context_diagnosis_report_total'),
        (access.CLINIC_LAB, clinic_report_total, 'context_clinic_report_total'),
        (access.ZONAL_LAB, zonal_report_total, 'context_zonal_report_total'),
        (access.CTRL_ISOLATES, zonal_report_total, 'context_ctrl_isolates_report_total'),
        (access.EDCS_TBLIS, edcs_tblis_report_total, 'context_edcs_tblis_report_total'),
    ]
    total = sum(
        processor(request).get(key, 0)
        for form, processor, key in sources
        if can_see_queries(request.user, form)
    )

    return {'context_specific_queries_total': total}
