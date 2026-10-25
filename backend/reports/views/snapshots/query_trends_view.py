# reports/views/snapshots/query_trends_view.py
import datetime
from collections import defaultdict

from django.db.models import Sum
from django.shortcuts import render

from reports.models import QueryCount, QuerySnapshotRun
from reports.services.query_snapshot import FORM_LABELS, is_visible
from utils import access
from utils.access import get_accessible_sites, is_unscoped
from utils.access_mixins import require_feature
from utils.roles import get_role_context

# Query types: forms not filled yet, and queries on the fields of filled forms
QUERY_TYPES = {"missing": "Missing forms", "form": "Form queries"}
GROUPS = {"zone": "Zone", "site": "Site", "form": "Form", "type": "Query type"}
DEFAULT_DAYS = 30


def _type(form):
    return "missing" if form == "missing_forms" else "form"


def _form_of(form, query):
    """The form a count is about: the missing form itself for missing-form counts."""
    return query if form == "missing_forms" else form


def _date(value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@require_feature(access.SNAPSHOTS)
def query_trends(request):
    """Open queries per day from the daily snapshots, per zone, site, form or query type."""
    user = request.user
    role_context = get_role_context(user)
    zones = {z.id: z.name for z in role_context.get("zones", [])}
    sites = {s.id: s.name for s in role_context.get("sites", [])}

    def pick(name, allowed):
        value = request.GET.get(name, "")
        return int(value) if value.isdigit() and int(value) in allowed else None

    zone_id, site_id = pick("zone", zones), pick("site", sites)
    query_type = request.GET.get("type") if request.GET.get("type") in QUERY_TYPES else ""
    forms = {k: v for k, v in FORM_LABELS.items() if k != "missing_forms"}
    form = request.GET.get("form") if request.GET.get("form") in forms else ""
    group = request.GET.get("group") if request.GET.get("group") in GROUPS else "zone"

    last_run = QuerySnapshotRun.objects.order_by("-snapshot_date").values_list("snapshot_date", flat=True).first()
    end = _date(request.GET.get("end")) or last_run or datetime.date.today()
    start = _date(request.GET.get("start")) or end - datetime.timedelta(days=DEFAULT_DAYS - 1)
    if start > end:
        start, end = end, start

    runs = list(QuerySnapshotRun.objects.filter(snapshot_date__range=(start, end)).order_by("snapshot_date"))
    dates = [run.snapshot_date for run in runs]

    # Per-site rows in the user's scope. Admins without a zone/site filter use the
    # all-sites rows for totals, counted in one pass exactly like the live pages.
    site_rows = QueryCount.objects.filter(run__in=runs, site__isnull=False)
    accessible = get_accessible_sites(user)
    if accessible is not None:
        site_rows = site_rows.filter(site__in=accessible)
    if zone_id:
        site_rows = site_rows.filter(zone_id=zone_id)
    if site_id:
        site_rows = site_rows.filter(site_id=site_id)
    use_all_sites = is_unscoped(user) and not zone_id and not site_id
    total_rows = QueryCount.objects.filter(run__in=runs, site__isnull=True) if use_all_sites else site_rows

    visible = {}

    def keep(f, q):
        if (f, q) not in visible:
            visible[(f, q)] = is_visible(user, f, q)
        return (visible[(f, q)]
                and (not query_type or _type(f) == query_type)
                and (not form or _form_of(f, q) == form))

    # Zone / site breakdowns need per-site rows; form / type use the totals rows
    source = site_rows if group in ("zone", "site") else total_rows
    fields = ["run__snapshot_date", "form", "query"]
    if group == "zone":
        fields.append("zone__name")
    elif group == "site":
        fields += ["site__name", "zone__name"]

    series = defaultdict(lambda: defaultdict(int))   # group label -> date -> count
    for r in source.values(*fields).annotate(n=Sum("count")):
        if not keep(r["form"], r["query"]):
            continue
        if group == "zone":
            label = r["zone__name"] or "No zone"
        elif group == "site":
            label = f'{r["site__name"]} ({r["zone__name"]})' if r["zone__name"] else r["site__name"]
        elif group == "form":
            label = FORM_LABELS.get(_form_of(r["form"], r["query"]), r["query"])
        else:
            label = QUERY_TYPES[_type(r["form"])]
        series[label][r["run__snapshot_date"]] += r["n"]

    totals = defaultdict(int)
    for r in total_rows.values("run__snapshot_date", "form", "query").annotate(n=Sum("count")):
        if keep(r["form"], r["query"]):
            totals[r["run__snapshot_date"]] += r["n"]
    total_line = [totals.get(d, 0) for d in dates]

    latest = dates[-1] if dates else None
    previous = dates[-2] if len(dates) > 1 else None
    first = dates[0] if dates else None
    kpis = {
        "latest": totals.get(latest, 0),
        "since_previous": totals.get(latest, 0) - totals.get(previous, 0) if previous else None,
        "since_start": totals.get(latest, 0) - totals.get(first, 0) if len(dates) > 1 else None,
        "peak": max(total_line) if total_line else 0,
    }

    days = list(reversed(dates))  # latest first
    table = sorted(
        (
            {
                "label": label,
                "days": [values.get(d, 0) for d in days],
                "change": values.get(latest, 0) - values.get(first, 0) if len(dates) > 1 else None,
            }
            for label, values in series.items()
        ),
        key=lambda row: (-(row["days"][0] if row["days"] else 0), row["label"]),
    )
    table_total = [sum(row["days"][i] for row in table) for i in range(len(days))]

    return render(request, "snapshots/query_trends.html", {
        "zones": zones, "sites": sites, "query_types": QUERY_TYPES, "groups": GROUPS, "forms": forms,
        "selected_zone": zone_id, "selected_site": site_id, "selected_type": query_type,
        "selected_form": form, "selected_group": group, "start": start, "end": end,
        "runs": runs, "latest": latest, "previous": previous, "first": first if previous else None, "kpis": kpis,
        "days": days, "table": table, "table_total": table_total, "group_label": GROUPS[group],
        "chart": {"labels": [d.isoformat() for d in dates], "total": total_line},
    })
