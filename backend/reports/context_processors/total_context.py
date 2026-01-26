from .screening_context      import screening_report_total
from .enrollment_context     import enrollment_report_total
from .forms_context          import forms_report_total
from .specific_queries_total import specific_queries_total   # ← import function directly


def global_total_issues(request):
    if not request.user.is_authenticated:
        return {'total_issues': 0}

    missing_forms_total = (
        forms_report_total(request)
        .get('forms_report_total', {})
        .get('total_missing', 0)
    )

    form_queries_total = (
        specific_queries_total(request)           # ← clean function call
        .get('specific_queries_total', 0)
    )

    grand_total = missing_forms_total + form_queries_total

    return {
        'total_issues': grand_total,
        'total_issues_components': {
            'missing_forms': missing_forms_total,
            'form_queries':  form_queries_total,
        }
    }