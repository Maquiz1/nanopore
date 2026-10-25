"""
Daily query counts for the Query trends page.

`take_snapshot()` counts every open query per site (and once for all sites) with
the same functions the live query pages and the sidebar use, so a day's snapshot
equals what the pages showed that day. Run it daily: `manage.py snapshot_queries`
(Celery Beat does this at 23:30).
"""
import time

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from reports.models import QueryCount, QuerySnapshotRun
from reports.services.clinic_dq import get_clinic_dq, get_clinic_queryset
from reports.services.diagnosis_dq import get_diagnosis_dq, get_diagnosis_queryset
from reports.services.enrollment_dq import get_enrollment_dq, get_enrollment_queryset
from reports.services.missing_form_dq_counts import get_missing_forms_counts
from reports.services.regimen_dq import get_regimen_dq, get_regimen_queryset
from reports.services.screening_dq import get_screening_dq, get_screening_queryset
from reports.services.zonal_dq import get_zonal_dq
from utils import access

# Queries the live pages count but leave out of their totals.
NOT_COUNTED = {("diagnosis", "long_treatment_qs")}
# Queries only admins see (screening shows "not eligible" to full-access users only).
ADMIN_ONLY = {("screening", "not_eligible")}


def _counts(totals, form):
    """count_<query> keys of a live service -> {query: count}."""
    return {
        key[len("count_"):]: n for key, n in totals.items()
        if key.startswith("count_") and (form, key[len("count_"):]) not in NOT_COUNTED
    }


def _missing_forms(user, site_id):
    counts = get_missing_forms_counts(user, site_id=site_id)
    return {form: counts[f"missing_{name}_count"] for name, form in MISSING_FORMS.items()}


# Missing-forms keys -> the form that is missing (also decides who sees it).
MISSING_FORMS = {
    "enrollment": access.ENROLLMENT,
    "clinic": access.CLINIC_LAB,
    "diagnosis": access.DIAGNOSIS,
    "regimen": access.REGIMEN,
    "zonal": access.ZONAL_LAB,
}

# (form key, label, counter(user, site_id) -> {query: count})
SOURCES = (
    ("screening", "Screening",
     lambda u, s: _counts(get_screening_dq(get_screening_queryset(u, None, s), u)[1], "screening")),
    ("enrollment", "Enrollment",
     lambda u, s: _counts(get_enrollment_dq(get_enrollment_queryset(u, None, s))[1], "enrollment")),
    ("clinic_lab", "Clinic Lab",
     lambda u, s: _counts(get_clinic_dq(get_clinic_queryset(u, None, s))[1], "clinic_lab")),
    ("diagnosis", "Diagnosis",
     lambda u, s: _counts(get_diagnosis_dq(get_diagnosis_queryset(u, None, s))[1], "diagnosis")),
    ("regimen", "Regimen",
     lambda u, s: _counts(get_regimen_dq(get_regimen_queryset(u, None, s))[1], "regimen")),
    ("zonal_lab", "Zonal Lab",
     lambda u, s: get_zonal_dq(u, apps.get_model("nanopore", "ZonalLaboratory"), None, s)[1]),
    ("edcs_tblis", "EDCS / TBLIS",
     lambda u, s: get_zonal_dq(u, apps.get_model("nanopore", "EdcsTblisZonal"), None, s)[1]),
    ("missing_forms", "Missing forms", _missing_forms),
)
FORM_LABELS = {form: label for form, label, _ in SOURCES}


def _system_user():
    """An unsaved superuser: sees every site, like the counts an admin gets."""
    return get_user_model()(username="query-snapshot", is_superuser=True)


def take_snapshot(snapshot_date=None):
    """Count today's open queries; re-running on the same day replaces that day's counts."""
    started = time.monotonic()
    Site = apps.get_model("locations", "Site")
    user = _system_user()
    snapshot_date = snapshot_date or timezone.localdate()

    sites = list(
        Site.objects.filter(screening__isnull=False).distinct()
        .select_related("district__region").order_by("name")
    )
    rows = []
    for site in [None] + sites:
        site_id = site.id if site else None
        zone_id = site.district.region.zone_id if site else None
        for form, _, counter in SOURCES:
            for query, n in counter(user, site_id).items():
                if n:
                    rows.append(QueryCount(zone_id=zone_id, site_id=site_id, form=form, query=query, count=n))

    with transaction.atomic():
        run, _ = QuerySnapshotRun.objects.update_or_create(
            snapshot_date=snapshot_date, defaults={"seconds": round(time.monotonic() - started, 1)},
        )
        run.counts.all().delete()
        for row in rows:
            row.run = run
        QueryCount.objects.bulk_create(rows)
    return run, len(rows)


def is_visible(user, form, query):
    """Query trends show every count in the viewer's zones/sites (the page is for people
    following query resolution: admins, data specialists/managers, coordinators)."""
    if (form, query) in ADMIN_ONLY:
        return access.AccessFlags(user).is_admin
    return True

