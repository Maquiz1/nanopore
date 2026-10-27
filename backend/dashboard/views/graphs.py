from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.views.generic import TemplateView

from nanopore.models import Screening
from nanopore.substudy import SUBSTUDIES, substudy_case
from utils.access import assigned_locations
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

# Lines get unreadable past this many series; then one "All" line is drawn
MAX_LINES = 8


def month_range(first, last):
    """Every month from first to last (inclusive), as date(year, month, 1)."""
    months, current = [], date(first.year, first.month, 1)
    while current <= last:
        months.append(current)
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)
    return months


class GraphsHomeView(LoginRequiredMixin, TemplateView):
    """Screening charts for the user's sites, by zone (or by site once a zone/site is chosen)."""
    template_name = "visual/visual_graphs.html"

    def filtered_queryset(self):
        qs = filter_queryset_by_user_role(self.request.user, Screening.objects.all(), site_field="site")
        get = self.request.GET.get
        if get("zone"):
            qs = qs.filter(site__district__region__zone_id=get("zone"))
        if get("site"):
            qs = qs.filter(site_id=get("site"))
        # Same date rules as the dashboard and the Participants list: either date works alone
        if get("start_date"):
            qs = qs.filter(screening_date__gte=get("start_date"))
        if get("end_date"):
            qs = qs.filter(screening_date__lte=get("end_date"))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user, get = self.request.user, self.request.GET.get
        role_context = get_role_context(user)
        zones = list(role_context["zones"])
        sites = list(role_context["sites"].select_related("district__region").order_by("name"))
        assigned_zones, assigned_sites = assigned_locations(user)
        context.update({
            "zones": zones, "sites": sites,
            "assigned_zones": assigned_zones, "assigned_sites": assigned_sites,
            "show_location_filter": len(sites) > 1,
            "selected": {key: get(key, "") for key in ("zone", "site", "start_date", "end_date")},
        })
        context["filters_active"] = any(context["selected"].values())

        qs = self.filtered_queryset()
        by_site = bool(get("zone") or get("site"))
        if by_site:
            key, name_key = "site_id", "site__name"
            # Only the chosen zone's (or the chosen) sites, so colours are counted within them
            in_view = [s for s in sites
                       if (not get("zone") or str(s.district.region.zone_id) == get("zone"))
                       and (not get("site") or str(s.id) == get("site"))]
            groups = sorted({(s.id, s.name) for s in in_view}, key=lambda g: g[1])
        else:
            key, name_key = "site__district__region__zone_id", "site__district__region__zone__name"
            groups = sorted({(z.id, z.name) for z in zones}, key=lambda g: g[1])
        group_word = "site" if by_site else "zone"

        totals = {row[key]: row["n"] for row in qs.values(key).annotate(n=Count("id"))}
        # Colour slot = place in the full alphabetical list, so a zone/site keeps its colour whatever is filtered
        slots = {gid: i for i, (gid, _) in enumerate(groups)}
        groups = [(gid, name) for gid, name in groups if totals.get(gid)]
        labels = [name for _, name in groups]

        today = timezone.localdate()
        first_of_month = today.replace(day=1)
        week = [today - timedelta(days=i) for i in range(6, -1, -1)]
        last7 = dict(qs.filter(screening_date__gte=week[0], screening_date__lte=today)
                     .values_list("screening_date").annotate(n=Count("id")))
        this_month = {row[key]: row["n"] for row in
                      qs.filter(screening_date__gte=first_of_month).values(key).annotate(n=Count("id"))}

        # Monthly trend, one line per group (or one total line when there are too many)
        monthly_rows = list(qs.annotate(month=TruncMonth("screening_date"))
                            .values(key, "month").annotate(n=Count("id")))
        months = month_range(min(r["month"] for r in monthly_rows), max(r["month"] for r in monthly_rows)) if monthly_rows else []
        if len(groups) <= MAX_LINES:
            per = {(r[key], r["month"]): r["n"] for r in monthly_rows}
            monthly_series = [{"label": name, "slot": slots[gid], "data": [per.get((gid, m), 0) for m in months]}
                              for gid, name in groups]
        else:
            per = {}
            for r in monthly_rows:
                per[r["month"]] = per.get(r["month"], 0) + r["n"]
            monthly_series = [{"label": "All", "slot": 0, "data": [per.get(m, 0) for m in months]}]

        # Substudy split per group (one definition: nanopore/substudy.py)
        split = {(r[key], r["sub"]): r["n"] for r in
                 qs.annotate(sub=substudy_case()).values(key, "sub").annotate(n=Count("id"))}
        substudy_series = [{"label": sub, "data": [split.get((gid, sub), 0) for gid, _ in groups]} for sub in SUBSTUDIES]

        total = sum(totals.values())
        context.update({
            "group_word": group_word,
            "total_screened": total,
            "last7_total": sum(last7.values()),
            "this_month_total": sum(this_month.values()),
            "first_of_month": first_of_month,
            "chart": {
                "groupWord": group_word,
                "byGroup": {"labels": labels, "data": [totals[gid] for gid, _ in groups]},
                "last7": {"labels": [d.strftime("%a %d %b") for d in week], "data": [last7.get(d, 0) for d in week]},
                "thisMonth": {"labels": labels, "data": [this_month.get(gid, 0) for gid, _ in groups]},
                "monthly": {"labels": [m.strftime("%b %Y") for m in months], "series": monthly_series},
                "substudy": {"labels": labels, "series": substudy_series},
            },
        })
        return context
