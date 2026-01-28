from .forms_context          import forms_report_total
from .specific_queries_total import specific_queries_total   # ← import function directly

def global_total_issues(request):
    if not request.user.is_authenticated:
        return {
            'total_issues': 0,
            'total_issues_components': {
                'missing_forms': 0,
                'form_queries':  0,
            }
        }

    # Missing forms — already role-filtered
    missing_forms_total = (
        forms_report_total(request)
        .get('forms_report_total', {})
        .get('total_form_missing', 0)
    )

    # Form queries — assuming you want similar logic here too
    # (if queries also have zonal vs others, apply the same pattern)
    form_queries_total = (
        specific_queries_total(request)
        .get('specific_queries_total', 0)
    )
    # ↑ If specific_queries_total also needs role filtering → update it similarly

    grand_total = missing_forms_total + form_queries_total

    return {
        'total_issues': grand_total,
        'total_issues_components': {
            'missing_forms': missing_forms_total,
            'form_queries':  form_queries_total,
        }
    }