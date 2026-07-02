from .form_missing.forms_context import forms_report_total
from .specific_queries_total import specific_queries_total   # ← import function directly
from nanopore.models import Screening
from django.db.models import Q
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

    # Calculate substudy counts
    base_qs = Screening.objects.filter(
        eligible=True,
        clinic_laboratory__isnull=False,
        tblis_laboratory__isnull=False
    ).filter(
        Q(tblis_laboratory__culture_performed__isnull=True) | 
        Q(tblis_laboratory__culture_performed__name__icontains='No') |
        Q(tblis_laboratory__culture_performed__name__exact='')
    )
    substudy2_count = base_qs.filter(clinic_laboratory__xpert_mtb_id__in=[2, 3, 4, 5, 6]).count()
    substudy4_count = base_qs.exclude(clinic_laboratory__xpert_mtb_id__in=[2, 3, 4, 5, 6]).count()

    return {
        'context_total_issues': grand_total,
        'context_total_issues_components': {
            'missing_forms': missing_forms_total,
            'form_queries':  form_queries_total,
        },
        'context_substudy2_count': substudy2_count,
        'context_substudy4_count': substudy4_count,
    }