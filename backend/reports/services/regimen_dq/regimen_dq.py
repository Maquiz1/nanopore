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

    # Sort by Zone → Site → PID
    qs = qs.order_by(
        "screening__site__district__region__zone__name",
        "screening__site__name",
        "screening__pid"
    )
    
    return qs


def get_regimen_dq(qs):
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
    
    # Reason = "Other, specify" (value 96)
    reason_is_96_q = (
        Q(reason__value=96) |
        Q(reason__name__iexact="96") |
        Q(reason__name__icontains="other")
    )

    missing_date = qs.filter(date__isnull=True)
    missing_drug = qs.filter(Q(drug__isnull=True) | Q(drug=""))
    missing_changes = qs.filter(changes__isnull=True)
    missing_reason = qs.filter(reason__isnull=True)

    # Other → specify must be filled (blank or spaces count as empty)
    missing_specify = qs.filter(reason_is_96_q).exclude(is_filled_char("specify"))

    # Any other reason → specify must be EMPTY (the web form saves an empty box as "")
    invalid_reason_filled = qs.filter(reason__isnull=False).exclude(reason_is_96_q).filter(
        is_filled_char("specify")
    )

    # Diagnosis 10(a) says the regimen was NOT changed, yet changes are recorded
    changes_when_not_changed = qs.filter(screening__diagnosis__regimen_changed__value=2)

    counts = {
        "missing_date": missing_date,
        "missing_drug": missing_drug,
        "missing_changes": missing_changes,
        "missing_reason": missing_reason,
        "missing_specify": missing_specify,
        "invalid_reason_filled": invalid_reason_filled,
        "changes_when_not_changed": changes_when_not_changed,
    }

    totals = {f"count_{k}": v.count() for k, v in counts.items()}
    totals["regimen_report_total"] = sum(totals.values())

    return counts, totals

