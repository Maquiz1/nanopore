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

        # ── Role context ─────────────────────────────────────────────
        role_context = get_role_context(request.user)
        is_admin     = role_context.get("is_admin", False)
        is_reviewer  = role_context.get("is_reviewer", False)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_superuser = request.user.is_superuser

        is_privileged = is_admin or is_reviewer or is_superuser

        # ── Zone / Site mappings ─────────────────────────────────────
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # ── GET params ───────────────────────────────────────────────
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else "All Zones"
        selected_site_name = sites.get(site_id_int, "") if site_id_int else "All Sites"

        overview = get_data_quality_overview(
            user=request.user,
            zone_id=zone_id_int,
            site_id=site_id_int,
        )

        context.update({
            **overview,
            "is_admin": is_admin,
            "is_reviewer": is_reviewer,
            "is_zonal_lab": is_zonal_lab,
            "is_privileged": is_privileged,

            "zones": zones,
            "sites": sites,

            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,
        })

        return context