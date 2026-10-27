from django.views.generic import TemplateView

from reports.services.queries_overview import queries_overview
from utils import access
from utils.access_mixins import AnyFormAccessMixin
from utils.roles import get_role_context


class QueriesOverviewView(AnyFormAccessMixin, TemplateView):
    """Queries overview: per form, queries on filled forms and forms not filled yet.
    The Missing forms / Form queries pages are the same page showing one of the two."""
    access_forms = access.ALL_FORMS
    template_name = "reports/data_quality/query_dashboard/queries_overview.html"
    section = "all"  # "all", "missing" or "queries"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_context = get_role_context(self.request.user)
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        def pick(name, allowed):
            value = self.request.GET.get(name, "")
            return int(value) if value.isdigit() and int(value) in allowed else None

        zone_id, site_id = pick("zone", zones), pick("site", sites)
        params = "&".join(f"{k}={v}" for k, v in (("zone", zone_id), ("site", site_id)) if v)
        context.update(queries_overview(self.request, zone_id, site_id))
        context.update({
            "section": self.section, "zones": zones, "sites": sites,
            "selected_zone": zone_id, "selected_site": site_id, "filter_query": params,
            "scope_label": sites.get(site_id) or zones.get(zone_id) or "All your sites",
            "filtered": bool(zone_id or site_id),
        })
        return context
