# reports/views/queries/substudy_queries_view.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.views import View
from django.shortcuts import render

from nanopore.substudy import substudy_case
from reports.services.substudy_queries import QUERIES_BY_KEY, substudy_query_qs, visible_queries
from utils.roles import get_role_context


class SubstudyQueriesView(LoginRequiredMixin, View):
    """Participants whose Zonal Lab / Diagnosis forms don't fit their substudy, with links to fix them."""
    template_name = "reports/data_quality/substudy/substudy_queries.html"
    paginate_by = 50

    def get(self, request, key=None):
        queries = visible_queries(request.user)
        if not queries:
            raise PermissionDenied

        role_context = get_role_context(request.user)
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        zone_id = int(zone_id) if zone_id and zone_id.isdigit() and int(zone_id) in zones else None
        site_id = int(site_id) if site_id and site_id.isdigit() and int(site_id) in sites else None

        tabs = [(query, substudy_query_qs(request.user, query, zone_id, site_id).count()) for query in queries]
        if key not in {query.key for query in queries}:
            # First query with something to fix, else the first one
            key = next((query.key for query, count in tabs if count), queries[0].key)
        selected = QUERIES_BY_KEY[key]

        show_accepted = request.GET.get("show") == "accepted"
        records = (
            substudy_query_qs(request.user, selected, zone_id, site_id, accepted=show_accepted)
            .select_related(
                "site__district__region__zone",
                "clinic_laboratory__xpert_mtb_rif_conducted",
                "clinic_laboratory__xpert_mtb",
                "zonal_laboratory",
                "enrollment",
                "diagnosis__tb_outcome2",
            )
            .annotate(substudy=substudy_case())
            .order_by("site__district__region__zone__name", "site__name", "pid")
        )
        page = Paginator(records, self.paginate_by).get_page(request.GET.get("page"))
        from reports.services.accepted import SUBSTUDY, holding, lapsed
        from reports.services.substudy_queries import substudy_values
        on_page = list(page.object_list)
        found = holding(SUBSTUDY, selected.key, on_page, substudy_values) if show_accepted else {}
        changed = set() if show_accepted else lapsed(SUBSTUDY, selected.key, on_page, substudy_values)
        for obj in on_page:
            obj.accepted_item, obj.accept_lapsed = found.get(str(obj.pk)), str(obj.pk) in changed

        filters = request.GET.copy()
        filters.pop("page", None)
        base = filters.copy()
        base.pop("show", None)
        return render(request, self.template_name, {
            "show_accepted": show_accepted, "accept_base": base.urlencode(),
            "accepted_total": substudy_query_qs(request.user, selected, zone_id, site_id, accepted=True).count(),
            "tabs": tabs,
            # Substudy 2 / 4 queries, then the uncategorized ones on their own row
            "tab_rows": [row for row in (
                [t for t in tabs if not t[0].key.startswith("uncategorized")],
                [t for t in tabs if t[0].key.startswith("uncategorized")],
            ) if row],
            "selected": selected,
            "page_obj": page,
            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id,
            "selected_site": site_id,
            "filter_query": filters.urlencode(),
        })
