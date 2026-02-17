# reports/context_processors/screening_context.py

from reports.services.screening_dq import get_screening_queryset, get_screening_dq


def screening_report_total(request):
    if not request.user.is_authenticated:
        return {"context_screening_report_total": 0}

    qs = get_screening_queryset(request.user)
    _, totals = get_screening_dq(qs)

    return {
        "context_screening_report_total": totals["screening_report_total"]
    }


# from django.apps import apps
# from django.db.models import Q, Count, F
# from utils.permissions import filter_queryset_by_user_role
# from utils.roles import get_role_context

# DAR_ES_SALAAM_ZONE_ID = 1  # Dar es Salaam zone ID


# def screening_report_total(request):
#     if not request.user.is_authenticated:
#         return {"screening_report_total": 0}

#     Screening = apps.get_model("nanopore", "Screening")

#     # ─────────────────────────────────────────────────────────────
#     # Base queryset with full location joins
#     # ─────────────────────────────────────────────────────────────
#     qs = Screening.objects.select_related(
#         "sex",
#         "enrolled",
#         "consent",
#         "reasons",
#         "site",
#         "site__district",
#         "site__district__region",
#         "site__district__region__zone",
#     )

#     # Role context
#     role_context = get_role_context(request.user)
#     is_zonal_lab = role_context.get("is_zonal_lab", False)
#     is_admin     = role_context.get("is_admin", False)
#     is_reviewer  = role_context.get("is_reviewer", False)
#     is_superuser = request.user.is_superuser
#     is_full_access = is_admin or is_superuser
#     is_privileged = is_admin or is_reviewer
    
#     # ─────────────────────────────────────────────────────────────
#     # Role-based filtering (SITE / REGION / ZONE)
#     # ─────────────────────────────────────────────────────────────
#     qs = filter_queryset_by_user_role(
#         request.user,
#         qs,
#         site_field="site"
#     )

#     # Non-eligible (role-aware)
#     if is_full_access:
#         not_eligible_count = qs.filter(eligible=False).count()
#     else:
#         not_eligible_count = 0
        
#     # ─────────────────────────────────────────────────────────────
#     # Optional UI filters
#     # ─────────────────────────────────────────────────────────────
#     # zone_id = request.GET.get("zone")
#     # site_id = request.GET.get("site")

#     # if zone_id:
#     #     qs = qs.filter(
#     #         site__district__region__zone_id=zone_id
#     #     )

#     # if site_id:
#     #     qs = qs.filter(
#     #         site_id=site_id
#     #     )
#     # ─────────────────────────────────────────────────────────────

#     # Missing/null fields
#     missing_screening_date      = qs.filter(screening_date__isnull=True).count()
#     missing_pid1                = qs.filter(pid1__isnull=True).count()
#     missing_pid2                = qs.filter(pid2__isnull=True).count()
#     missing_sex                 = qs.filter(sex__isnull=True).count()
#     missing_age_or_dob          = qs.filter(age__isnull=True, dob__isnull=True).count()
#     missing_consent             = qs.filter(consent__isnull=True).count()
#     missing_age18years          = qs.filter(age18years__isnull=True).count()
#     missing_produce_resp_sample = qs.filter(produce_resp_sample__isnull=True).count()
#     missing_genexpert_confirm   = qs.filter(genexpert_confirmation__isnull=True).count()
#     missing_unable_understand   = qs.filter(unable_understand__isnull=True).count()
#     missing_not_willing         = qs.filter(not_willing__isnull=True).count()
#     missing_enrolled            = qs.filter(enrolled__isnull=True).count()

#     # Conditional missing fields
#     missing_reasons_when_no = qs.filter(
#         enrolled__name__iexact="no",
#         reasons__isnull=True
#     ).count()

#     missing_consent_date_when_yes = qs.filter(
#         consent__name__iexact="yes",
#         consent_date__isnull=True
#     ).count()

#     missing_reasons_other = qs.filter(
#         reasons__value=96,
#         reasons_other__isnull=True
#     ).count()

#     # Zone-specific rules
#     missing_present_symptoms = qs.filter(
#         site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID,
#         present_symptoms__isnull=True
#     ).count()

#     missing_genexpert_confirm = qs.exclude(
#         site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID
#     ).filter(
#         genexpert_confirmation__isnull=True
#     ).count()

#     # PID quality issues
#     duplicate_pid_count = qs.values("pid").annotate(
#         cnt=Count("id")
#     ).filter(cnt__gt=1).count()

#     mismatched_pid_count = qs.filter(
#         ~Q(pid1=F("pid2")),
#         pid1__isnull=False,
#         pid2__isnull=False
#     ).count()

#     invalid_length_pid_count = qs.filter(
#         pid__isnull=False,
#         pid__regex=r'^(?!.{16}$).*$'
#     ).count()
        
#     # Grand total – in your specified order
#     total_issues = (
#         duplicate_pid_count +
#         invalid_length_pid_count +
#         mismatched_pid_count +
#         missing_pid1 +
#         missing_pid2 +
#         not_eligible_count +
#         missing_screening_date +
#         missing_sex +
#         missing_age_or_dob +
#         missing_consent +
#         missing_consent_date_when_yes +
#         missing_age18years +
#         missing_present_symptoms +
#         missing_genexpert_confirm +
#         missing_produce_resp_sample +
#         missing_unable_understand +
#         missing_not_willing +
#         missing_enrolled +
#         missing_reasons_when_no +
#         missing_reasons_other
#     )

#     return {
#         "context_screening_report_total": total_issues,
#         "missing_consent_date_when_yes": missing_consent_date_when_yes,
#         "missing_reasons_other": missing_reasons_other,
#         "duplicate_pid_count": duplicate_pid_count,
#         "mismatched_pid_count": mismatched_pid_count,
#         "invalid_length_pid_count": invalid_length_pid_count,
#         "not_eligible_count": not_eligible_count,
#         "missing_screening_date": missing_screening_date,
#         "missing_pid1": missing_pid1,
#         "missing_pid2": missing_pid2,
#         "missing_sex": missing_sex,
#         "missing_age_or_dob": missing_age_or_dob,
#         "missing_consent": missing_consent,
#         "missing_age18years": missing_age18years,
#         "missing_present_symptoms": missing_present_symptoms,
#         "missing_produce_resp_sample": missing_produce_resp_sample,
#         "missing_genexpert_confirm": missing_genexpert_confirm,
#         "missing_unable_understand": missing_unable_understand,
#         "missing_not_willing": missing_not_willing,
#         "missing_enrolled": missing_enrolled,
#         "missing_reasons_when_no": missing_reasons_when_no,
#     }