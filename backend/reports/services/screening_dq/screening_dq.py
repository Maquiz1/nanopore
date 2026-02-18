from django.apps import apps
from django.db.models import Q, F, Count
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

DAR_ES_SALAAM_ZONE_ID = 1

def get_screening_queryset(user, zone_id=None, site_id=None):
    Screening = apps.get_model("nanopore", "Screening")
    qs = Screening.objects.select_related("site", "site__district__region__zone")
    qs = filter_queryset_by_user_role(user, qs, site_field="site")

    if zone_id:
        qs = qs.filter(site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(site_id=site_id)

    return qs


def get_screening_dq(qs, user=None):
    """
    Returns:
        problem_lists: dict of querysets for each DQ issue
        totals: dict of counts for each issue
        screening_report_total: total number of issues (sum of relevant counts)
    """

    # ── MISSING FIELDS ──
    missing_screening_date = qs.filter(screening_date__isnull=True)
    missing_pid1 = qs.filter(pid1__isnull=True)
    missing_pid2 = qs.filter(pid2__isnull=True)
    missing_sex = qs.filter(sex__isnull=True)
    missing_age_dob = qs.filter(age__isnull=True, dob__isnull=True)
    missing_consent = qs.filter(consent__isnull=True)
    missing_age18years = qs.filter(age18years__isnull=True)
    missing_produce_resp_sample = qs.filter(produce_resp_sample__isnull=True)
    missing_unable_understand = qs.filter(unable_understand__isnull=True)
    missing_not_willing = qs.filter(not_willing__isnull=True)
    missing_enrolled = qs.filter(enrolled__isnull=True)
    missing_reasons = qs.filter(enrolled__name__iexact="no", reasons__isnull=True)
    missing_consent_date_when_yes = qs.filter(consent__name__iexact="yes", consent_date__isnull=True)
    missing_reasons_other = qs.filter(reasons__value=96, reasons_other__isnull=True)
    missing_present_symptoms = qs.filter(
        site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID,
        present_symptoms__isnull=True
    )
    missing_genexpert_confirmation = qs.exclude(
        site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID
    ).filter(genexpert_confirmation__isnull=True)

    # ── PID ISSUES ──
    duplicate_pids_qs = qs.values("pid").annotate(pid_count=Count("id")).filter(pid_count__gt=1)
    duplicate_pids = qs.filter(pid__in=[p["pid"] for p in duplicate_pids_qs])
    mismatched_pids = qs.filter(~Q(pid1=F("pid2")), pid1__isnull=False, pid2__isnull=False)
    invalid_length_pids = qs.filter(pid__isnull=False, pid__regex=r"^(?!.{16}$).*$")

    # ── NON-ELIGIBLE ──
    is_full_access = False
    if user:
        role_context = get_role_context(user)
        is_admin = role_context.get("is_admin", False)
        is_superuser = user.is_superuser
        is_full_access = is_admin or is_superuser

    not_eligible_qs = qs.filter(eligible=False) if is_full_access else qs.none()

    # ── PROBLEM LISTS ──
    problem_lists = {
        "missing_screening_date": missing_screening_date,
        "missing_pid1": missing_pid1,
        "missing_pid2": missing_pid2,
        "missing_sex": missing_sex,
        "missing_age_dob": missing_age_dob,
        "missing_consent": missing_consent,
        "missing_age18years": missing_age18years,
        "missing_produce_resp_sample": missing_produce_resp_sample,
        "missing_unable_understand": missing_unable_understand,
        "missing_not_willing": missing_not_willing,
        "missing_enrolled": missing_enrolled,
        "missing_reasons": missing_reasons,
        "missing_consent_date_when_yes": missing_consent_date_when_yes,
        "missing_reasons_other": missing_reasons_other,
        "missing_present_symptoms": missing_present_symptoms,
        "missing_genexpert_confirmation": missing_genexpert_confirmation,
        "duplicate_pids": duplicate_pids,       # always counted
        "mismatched_pids": mismatched_pids,
        "invalid_length_pids": invalid_length_pids,
        "not_eligible": not_eligible_qs,       # counted only if full access
    }

    # ── TOTALS ──
    totals = {}
    for key, qs_item in problem_lists.items():
        # not_eligible counts only for full access
        if key == "not_eligible" and not is_full_access:
            totals[f"count_{key}"] = 0
        else:
            totals[f"count_{key}"] = qs_item.count()
    
    # Screening report total = sum of all counts
    screening_report_total = sum(totals.values())
    totals["screening_report_total"] = screening_report_total

    return problem_lists, totals
