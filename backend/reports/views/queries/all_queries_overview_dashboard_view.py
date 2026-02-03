from django.views.generic import TemplateView
from django.apps import apps
from utils.roles import get_role_context
from utils.permissions import filter_queryset_by_user_role
from reports.services.overview_dq_counts import get_data_quality_overview

class AllOverviewQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/all_queries_overview_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        role_context = get_role_context(request.user)

        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        overview = get_data_quality_overview(
            user=request.user,
            zone_id=zone_id_int,
            site_id=site_id_int,
        )

        context.update({
            **overview,
            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
        })

        return context