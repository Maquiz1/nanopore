from .form_missing.forms_context import forms_report_total
from .specific_queries_total import specific_queries_total   # ← import function directly
from utils.roles import get_role_context
from utils.permissions import filter_queryset_by_user_role

def global_total_issues(request):
    if not request.user.is_authenticated:
        return {
            'total_issues': 0,
            'total_issues_components': {
                'missing_forms': 0,
                'form_queries':  0,
            }
        }
        
        
    role_context = get_role_context(request.user)
    is_zonal_lab = role_context.get("is_zonal_lab", False)
    is_admin     = role_context.get("is_admin", False)
    is_reviewer  = role_context.get("is_reviewer", False)
    is_superuser = request.user.is_superuser
    is_full_access = is_admin or is_superuser
    is_privileged = is_admin or is_reviewer

    # Missing forms — already role-filtered
    missing_forms_total = (
        forms_report_total(request)
        .get('context_forms_report_total', {})
        .get('context_total_form_missing', 0)
    )

    # Form queries — assuming you want similar logic here too
    # (if queries also have zonal vs others, apply the same pattern)
    form_queries_total = (
        specific_queries_total(request)
        .get('context_specific_queries_total', 0)
    )
    # ↑ If specific_queries_total also needs role filtering → update it similarly

    grand_total = missing_forms_total + form_queries_total

    return {
        'context_total_issues': grand_total,
        'context_total_issues_components': {
            'missing_forms': missing_forms_total,
            'form_queries':  form_queries_total,
        }
    }