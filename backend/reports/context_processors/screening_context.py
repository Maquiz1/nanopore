# utils/context_processors.py  (or wherever you keep these)
from django.apps import apps
from django.db.models import Q, Count, Exists, OuterRef,F
from utils.permissions import filter_queryset_by_user_role


def screening_report_total(request):
    """
    Computes total data quality issues in Screening records visible to the current user.
    
    Issues include:
    - Missing required/important fields
    - PID-related problems (duplicates, mismatch, invalid length)
    - Non-eligible records (if you want to flag them as quality concern)
    - Inconsistent enrollment logic (e.g. enrolled=Yes but no reason)
    
    Returns flat number under "screening_report_total" for navbar/dashboard use.
    """
    if not request.user.is_authenticated:
        return {"screening_report_total": 0}

    Screening = apps.get_model("nanopore", "Screening")

    # Base queryset — scoped by user role/site
    screenings = Screening.objects.select_related(
        "sex",           # helps with missing_sex
        "enrolled",      # helps with enrolled__name
    ).prefetch_related(  # optional — only if you later need related objects
        # "site", "site__district__region__zone",  # already handled by filter_queryset
    )

    screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

    # ── Missing / null fields ────────────────────────────────────────────────
    missing_screening_date      = screenings.filter(screening_date__isnull=True).count()
    missing_pid1                = screenings.filter(pid1__isnull=True).count()
    missing_pid2                = screenings.filter(pid2__isnull=True).count()
    missing_sex                 = screenings.filter(sex__isnull=True).count()
    missing_age_or_dob          = screenings.filter(age__isnull=True, dob__isnull=True).count()
    missing_consent             = screenings.filter(consent__isnull=True).count()
    missing_age18years          = screenings.filter(age18years__isnull=True).count()
    missing_present_symptoms    = screenings.filter(present_symptoms__isnull=True).count()
    missing_produce_resp_sample = screenings.filter(produce_resp_sample__isnull=True).count()
    missing_genexpert_confirm   = screenings.filter(genexpert_confirmation__isnull=True).count()
    missing_unable_understand   = screenings.filter(unable_understand__isnull=True).count()
    missing_not_willing         = screenings.filter(not_willing__isnull=True).count()
    missing_enrolled            = screenings.filter(enrolled__isnull=True).count()

    # Only count missing reasons when enrolled = Yes
    missing_reasons_when_enrolled = screenings.filter(
        enrolled__name__iexact="yes",
        reasons__isnull=True
    ).count()

    # ── PID quality issues ──────────────────────────────────────────────────
    # Duplicates (same pid used more than once)
    duplicate_pids = screenings.values("pid").annotate(
        pid_count=Count("id")
    ).filter(pid_count__gt=1)
    duplicate_pid_count = duplicate_pids.count()

    # PID1 != PID2 (when both filled)
    mismatched_pid_count = screenings.filter(
        ~Q(pid1=F("pid2")),
        pid1__isnull=False,
        pid2__isnull=False
    ).count()

    # Invalid PID length (not exactly 16 chars)
    invalid_length_pid_count = screenings.filter(
        pid__isnull=False,
        pid__exact=""
    ).exclude(
        pid__regex=r"^.{16}$"
    ).count()

    # ── Eligibility flag ────────────────────────────────────────────────────
    # Optional: count non-eligible as a quality concern
    # (you can remove this line if you don't want to include it)
    not_eligible_count = screenings.filter(eligible=False).count()

    # ── Total issues ────────────────────────────────────────────────────────
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
        missing_reasons_when_enrolled +
        duplicate_pid_count +
        mismatched_pid_count +
        invalid_length_pid_count +
        not_eligible_count
    )

    return {"screening_report_total": total_issues}