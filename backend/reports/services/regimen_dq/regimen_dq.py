# reports/services/regimen_dq.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role


def get_regimen_queryset(user, zone_id=None, site_id=None):
    RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

    qs = RegimenChanges.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district",
        "screening__site__district__region",
        "screening__site__district__region__zone",
        "changes",
        "reason",
    )

    qs = filter_queryset_by_user_role(user, qs, site_field="screening__site")

    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)

    if site_id:
        qs = qs.filter(screening__site_id=site_id)

    return qs


def get_regimen_dq(qs):
    reason_is_96_q = (
        Q(reason__value=96) |
        Q(reason__name__iexact="96") |
        Q(reason__name__iexact="other")
    )

    missing_date = qs.filter(date__isnull=True)
    missing_drug = qs.filter(Q(drug__isnull=True) | Q(drug=""))
    missing_changes = qs.filter(changes__isnull=True)
    missing_reason = qs.filter(reason__isnull=True)

    missing_specify = qs.filter(reason_is_96_q).filter(
        Q(specify__isnull=True) | Q(specify="")
    )

    counts = {
        "missing_date": missing_date,
        "missing_drug": missing_drug,
        "missing_changes": missing_changes,
        "missing_reason": missing_reason,
        "missing_specify": missing_specify,
    }

    totals = {f"count_{k}": v.count() for k, v in counts.items()}
    totals["regimen_report_total"] = sum(totals.values())

    return counts, totals

