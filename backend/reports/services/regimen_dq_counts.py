# reports/services/regimen_dq_counts.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role

def get_regimen_dq_counts(user, zone_id=None, site_id=None):
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

    # missing fields
    missing_date_qs = qs.filter(date__isnull=True)
    missing_drug_qs = qs.filter(Q(drug__isnull=True) | Q(drug__exact=""))
    missing_changes_qs = qs.filter(changes__isnull=True)
    missing_reason_qs = qs.filter(reason__isnull=True)

    # reason = Other (96)
    reason_is_96_q = Q(reason__value=96) | Q(reason__name__iexact="96") | Q(reason__name__iexact="other")
    missing_specify_qs = qs.filter(reason_is_96_q).filter(Q(specify__isnull=True) | Q(specify__exact=""))

    counts = {
        "count_missing_date": missing_date_qs.count(),
        "count_missing_drug": missing_drug_qs.count(),
        "count_missing_changes": missing_changes_qs.count(),
        "count_missing_reason": missing_reason_qs.count(),
        "count_missing_specify_when_other": missing_specify_qs.count(),
    }

    counts["regimen_report_total"] = sum(counts.values())
    counts["total_issues"] = counts["regimen_report_total"]

    return counts