# reports/services/screening_dq_counts.py
from django.apps import apps
from django.db.models import Q, F, Count
from utils.permissions import filter_queryset_by_user_role

DAR_ES_SALAAM_ZONE_ID = 1

def get_screening_dq_counts(user, zone_id=None, site_id=None):
    Screening = apps.get_model("nanopore", "Screening")
    qs = Screening.objects.select_related("site", "site__district__region__zone")
    qs = filter_queryset_by_user_role(user, qs, site_field="site")

    # Apply zone/site filters
    if zone_id:
        qs = qs.filter(site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(site_id=site_id)

    # Missing fields
    missing_screening_date_qs = qs.filter(screening_date__isnull=True)
    missing_pid1_qs = qs.filter(pid1__isnull=True)
    missing_pid2_qs = qs.filter(pid2__isnull=True)
    missing_sex_qs = qs.filter(sex__isnull=True)
    missing_age_dob_qs = qs.filter(age__isnull=True, dob__isnull=True)
    missing_consent_qs = qs.filter(consent__isnull=True)
    missing_age18years_qs = qs.filter(age18years__isnull=True)
    missing_produce_resp_sample_qs = qs.filter(produce_resp_sample__isnull=True)
    missing_unable_qs = qs.filter(unable_understand__isnull=True)
    missing_not_willing_qs = qs.filter(not_willing__isnull=True)
    missing_enrolled_qs = qs.filter(enrolled__isnull=True)

    missing_reasons_qs = qs.filter(enrolled__name__iexact="no", reasons__isnull=True)
    missing_consent_date_when_yes_qs = qs.filter(consent__name__iexact="yes", consent_date__isnull=True)
    missing_reasons_other_qs = qs.filter(reasons__value=96, reasons_other__isnull=True)

    missing_present_symptoms_qs = qs.filter(
        site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID,
        present_symptoms__isnull=True
    )

    missing_genexpert_qs = qs.exclude(
        site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID
    ).filter(genexpert_confirmation__isnull=True)

    # PID issues
    duplicate_pids_count = qs.values("pid").annotate(pid_count=Count("id")).filter(pid_count__gt=1).count()
    mismatched_pids_count = qs.filter(~Q(pid1=F("pid2")), pid1__isnull=False, pid2__isnull=False).count()
    invalid_length_pids_count = qs.filter(pid__isnull=False, pid__regex=r"^(?!.{16}$).*$").count()

    # Non-eligible (role-aware)
    from utils.roles import get_role_context
    role_context = get_role_context(user)
    is_admin = role_context.get("is_admin", False)
    is_superuser = user.is_superuser
    is_full_access = is_admin or is_superuser

    if is_full_access:
        count_not_eligible = qs.filter(eligible=False).count()
    else:
        count_not_eligible = 0

    counts = {
        "count_missing_screening_date": missing_screening_date_qs.count(),
        "count_missing_pid1": missing_pid1_qs.count(),
        "count_missing_pid2": missing_pid2_qs.count(),
        "count_missing_sex": missing_sex_qs.count(),
        "count_missing_age_dob": missing_age_dob_qs.count(),
        "count_missing_consent": missing_consent_qs.count(),
        "count_missing_age18years": missing_age18years_qs.count(),
        "count_missing_present_symptoms": missing_present_symptoms_qs.count(),
        "count_missing_genexpert_confirmation": missing_genexpert_qs.count(),
        "count_missing_produce_resp_sample": missing_produce_resp_sample_qs.count(),
        "count_missing_unable_understand": missing_unable_qs.count(),
        "count_missing_not_willing": missing_not_willing_qs.count(),
        "count_missing_enrolled": missing_enrolled_qs.count(),
        "count_missing_reasons": missing_reasons_qs.count(),
        "count_missing_consent_date_when_yes": missing_consent_date_when_yes_qs.count(),
        "count_missing_reasons_other": missing_reasons_other_qs.count(),
        "count_duplicate_pids": duplicate_pids_count,
        "count_mismatched_pids": mismatched_pids_count,
        "count_invalid_length_pids": invalid_length_pids_count,
        "count_not_eligible": count_not_eligible,
    }

    # Total issues (sum in the same order as view)
    counts["total_issues"] = sum(counts.values())

    return counts
