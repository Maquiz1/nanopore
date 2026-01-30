# reports/context_processors.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role


def regimen_report_total(request):
    """
    Navbar count for Regimen Changes data quality issues.

    Based on model fields:
    - date: DateField (blank=True, null=True)
    - drug: CharField (blank=True, null=True)
    - changes: ForeignKey to RegimenTypeOfChange (blank=True, null=True)
    - reason: ForeignKey to RegimenReasonForChange (blank=True, null=True)
    - specify: TextField (blank=True, null=True)

    Issues counted:
    - Missing date
    - Missing drug
    - Missing type of change (changes)
    - Missing specify → only when reason == 96 (Other / requires specification)

    Note: missing reason is NO LONGER counted (even when changes == 96)
    """
    if not request.user.is_authenticated:
        return {
            "regimen_report_total": 0,
            "missing_regimen_date": 0,
            "missing_regimen_drug": 0,
            "missing_regimen_changes": 0,
            "missing_regimen_reason": 0,
            "missing_regimen_specify_when_other": 0,
        }

    RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

    # ─────────────────────────────────────────────────────────────
    # Base queryset with full location joins
    # ─────────────────────────────────────────────────────────────
    regimens = RegimenChanges.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district",
        "screening__site__district__region",
        "screening__site__district__region__zone",
        "reason",
        "changes",
    )

    # ─────────────────────────────────────────────────────────────
    # Apply role-based filtering (SITE + ZONE handled here)
    # ─────────────────────────────────────────────────────────────
    regimens = filter_queryset_by_user_role(
        request.user,
        regimens,
        site_field="screening__site",
    )

    # ─────────────────────────────────────────────────────────────
    # Optional filtering from UI (GET params)
    # ─────────────────────────────────────────────────────────────
    # zone_id = request.GET.get("zone")
    # site_id = request.GET.get("site")

    # if zone_id:
    #     regimens = regimens.filter(
    #         screening__site__district__region__zone_id=zone_id
    #     )

    # if site_id:
    #     regimens = regimens.filter(
    #         screening__site_id=site_id
    #     )


    # ── Q helper for "Other" in reason ──────────────────────────────────────
    # Adjust according to your RegimenReasonForChange model
    # Most reliable if using integer choices:
    # reason_is_96_q = Q(reason__value=96)
    # Safer / more flexible version (uncomment if needed):
    reason_is_96_q = (
        Q(reason__value=96) |
        Q(reason__name__iexact="96") |
        Q(reason__name__iexact="other")
    )

    # ── Missing field counts ────────────────────────────────────────────────
    missing_regimen_date = regimens.filter(date__isnull=True).count()
    missing_regimen_drug = regimens.filter(drug__isnull=True).count()
    missing_regimen_changes = regimens.filter(changes__isnull=True).count()
    missing_regimen_reason = regimens.filter(reason__isnull=True).count()

    # Specify is only required/checked when reason == 96
    missing_regimen_specify_when_other = regimens.filter(
        reason_is_96_q,
        specify__isnull=True
    ).count()

    # ── Aggregate total issues ──────────────────────────────────────────────
    regimen_report_total = (
        missing_regimen_date
        + missing_regimen_drug
        + missing_regimen_changes
        + missing_regimen_reason
        + missing_regimen_specify_when_other
    )

    return {
        "regimen_report_total": regimen_report_total,
        "missing_regimen_date": missing_regimen_date,
        "missing_regimen_drug": missing_regimen_drug,
        "missing_regimen_changes": missing_regimen_changes,
        "missing_regimen_reason": missing_regimen_reason,
        "missing_regimen_specify_when_other": missing_regimen_specify_when_other,
    }