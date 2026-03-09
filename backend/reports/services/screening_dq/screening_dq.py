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

    # Sort by Zone → Site → PID
    qs = qs.order_by(
        "site__district__region__zone__name",
        "site__name",
        "pid"
    )
    
    return qs


def get_screening_dq(qs, user=None):
    """
    Returns:
        problem_lists: dict of querysets for each DQ issue
        totals: dict of counts for each issue
    """
    def is_true(field):
        """
        Field is explicitly True
        """
        return Q(**{field: True})


    def is_false(field):
        """
        Field is explicitly False
        """
        return Q(**{field: False})


    def is_checked(field):
        """
        Checkbox is checked (True)
        """
        return Q(**{field: True})


    def is_unchecked(field):
        """
        Checkbox is False OR NULL (treat as not checked)
        Useful when BooleanField(null=True)
        """
        return Q(**{field: False}) | Q(**{f"{field}__isnull": True})

    
    def is_filled_char(field):
        return (
            Q(**{f"{field}__isnull": False}) &
            ~Q(**{f"{field}__regex": r'^\s*$'})
        )

    def is_filled_non_char(field):
        return Q(**{f"{field}__isnull": False})
    
    def m2m_has_any(field):
        return Q(**{f"{field}__isnull": False})

    # ── ROLE CHECK ──
    is_full_access = False
    if user:
        role_context = get_role_context(user)
        is_admin = role_context.get("is_admin", False)
        is_superuser = user.is_superuser
        is_full_access = is_admin or is_superuser

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
    missing_consent_date_when_yes = qs.filter(
        consent__name__iexact="yes",
        consent_date__isnull=True
    )
    missing_reasons_other = qs.filter(
        reasons__value=96,
        reasons_other__isnull=True
    )

    missing_present_symptoms = qs.filter(
        site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID,
        present_symptoms__isnull=True
    )

    missing_genexpert_confirmation = qs.exclude(
        site__district__region__zone_id=DAR_ES_SALAAM_ZONE_ID
    ).filter(genexpert_confirmation__isnull=True)

    # ── PID ISSUES ──
    duplicate_pids_qs = (
        qs.values("pid")
        .annotate(pid_count=Count("id"))
        .filter(pid_count__gt=1)
    )

    duplicate_pids = qs.filter(
        pid__in=[p["pid"] for p in duplicate_pids_qs]
    )

    mismatched_pids = qs.filter(
        ~Q(pid1=F("pid2")),
        pid1__isnull=False,
        pid2__isnull=False
    )

    invalid_length_pids = qs.filter(
        pid__isnull=False,
        pid__regex=r"^(?!.{16}$).*$"
    )
    
    
    # ────────────────
    # ENROLLED / REASONS / CONSENT RULES
    # ────────────────

    # 1️⃣ Rule 1 — enrolled = 1 → reasons must be empty
    enrolled_1_q = Q(enrolled=1) | Q(enrolled__value=1) | Q(enrolled__name__iexact="1")

    invalid_enrolled_1 = qs.filter(
        enrolled_1_q & is_filled_non_char("reasons")
    )

    # 2️⃣ Rule 2 — reasons = 1 → reasons_other must be empty
    reasons_1_q = Q(reasons=1) | Q(reasons__value=1) | Q(reasons__name__iexact="1")

    invalid_reasons_1 = qs.filter(
        reasons_1_q & is_filled_char("reasons_other")
    )

    # ────────────────
    # Combine all rules if needed
    # ────────────────
    invalid_enrollment_rules = invalid_enrolled_1 | invalid_reasons_1

    # 3️⃣ Rule 3 — consent = 2 → consent_date must be empty
    consent_2_q = Q(consent=2) | Q(consent__value=2) | Q(consent__name__iexact="2")

    invalid_consent_2 = qs.filter(
        consent_2_q & is_filled_non_char("consent_date")
    )

    # ── NON-ELIGIBLE (ROLE CONTROLLED) ──
    if is_full_access:
        not_eligible_qs = qs.filter(eligible=False)
    else:
        not_eligible_qs = qs.none()

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
        "duplicate_pids": duplicate_pids,
        "mismatched_pids": mismatched_pids,
        "invalid_length_pids": invalid_length_pids,
        "not_eligible": not_eligible_qs,  # always present, but may be empty
        "invalid_enrollment_rules":invalid_enrollment_rules,
        "invalid_consent_2":invalid_consent_2,
    }

    # ── TOTALS ──
    totals = {
        f"count_{key}": qs_item.count()
        for key, qs_item in problem_lists.items()
    }

    totals["screening_report_total"] = sum(totals.values())

    return problem_lists, totals
