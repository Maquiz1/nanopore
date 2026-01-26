# utils/context_processors.py
from django.apps import apps
from django.db.models import Q, Count, F
from utils.permissions import filter_queryset_by_user_role


def screening_report_total(request):
    """
    Computes total data quality issues in Screening records visible to the current user.
    
    Returns a dict with key 'screening_report_total' containing the sum of all detected issues.
    Some records may contribute to multiple categories (hence it's not a distinct record count).
    """
    if not request.user.is_authenticated:
        return {"screening_report_total": 0}

    Screening = apps.get_model("nanopore", "Screening")

    # Base queryset — scoped by user role/site
    qs = Screening.objects.select_related(
        "sex",
        "enrolled",
    )

    qs = filter_queryset_by_user_role(request.user, qs, site_field="site")

    # ──────────────────────────────────────────────────────────────
    # Missing / null fields
    # ──────────────────────────────────────────────────────────────
    missing_screening_date      = qs.filter(screening_date__isnull=True).count()
    missing_pid1                = qs.filter(pid1__isnull=True).count()
    missing_pid2                = qs.filter(pid2__isnull=True).count()
    missing_sex                 = qs.filter(sex__isnull=True).count()
    missing_age_or_dob          = qs.filter(age__isnull=True, dob__isnull=True).count()
    missing_consent             = qs.filter(consent__isnull=True).count()
    missing_age18years          = qs.filter(age18years__isnull=True).count()
    missing_present_symptoms    = qs.filter(present_symptoms__isnull=True).count()
    missing_produce_resp_sample = qs.filter(produce_resp_sample__isnull=True).count()
    missing_genexpert_confirm   = qs.filter(genexpert_confirmation__isnull=True).count()
    missing_unable_understand   = qs.filter(unable_understand__isnull=True).count()
    missing_not_willing         = qs.filter(not_willing__isnull=True).count()
    missing_enrolled            = qs.filter(enrolled__isnull=True).count()

    # Only when enrolled = "Yes" but no reason
    missing_reasons_when_yes = qs.filter(
        enrolled__name__iexact="yes",
        reasons__isnull=True
    ).count()

    # ──────────────────────────────────────────────────────────────
    # PID quality issues
    # ──────────────────────────────────────────────────────────────
    duplicate_pid_count = qs.values("pid").annotate(
        cnt=Count("id")
    ).filter(cnt__gt=1).count()

    mismatched_pid_count = qs.filter(
        ~Q(pid1=F("pid2")),
        pid1__isnull=False,
        pid2__isnull=False
    ).count()

    # Fixed: pid__exact="" was wrong – we want non-exact length 16
    invalid_length_pid_count = qs.filter(
        pid__isnull=False,
        pid__regex=r'^(?!.{16}$).*$'   # anything that is NOT exactly 16 characters
    ).count()

    # ──────────────────────────────────────────────────────────────
    # Optional: non-eligible as quality issue
    # ──────────────────────────────────────────────────────────────
    not_eligible_count = qs.filter(eligible=False).count()

    # ──────────────────────────────────────────────────────────────
    # Grand total (sum of all issue types)
    # ──────────────────────────────────────────────────────────────
    total_issues = (
        missing_screening_date +
        missing_pid1 +
        missing_pid2 +
        missing_sex +
        missing_age_or_dob +
        missing_consent +
        missing_age18years +
        missing_present_symptoms +
        missing_produce_resp_sample +
        missing_genexpert_confirm +
        missing_unable_understand +
        missing_not_willing +
        missing_enrolled +
        missing_reasons_when_yes +
        duplicate_pid_count +
        mismatched_pid_count +
        invalid_length_pid_count +
        not_eligible_count
    )

    return {"screening_report_total": total_issues}