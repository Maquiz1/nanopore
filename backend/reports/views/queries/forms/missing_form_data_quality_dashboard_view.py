# reports/views/missing_form_dashboard.py

from django.views.generic import TemplateView
from utils.roles import get_role_context
from reports.services.missing_form_dq import get_missing_forms_dq


class MissingFormDataQualityDashboardView(TemplateView):
    template_name = (
        "reports/data_quality/query_dashboard/"
        "missing_form_queries_dashboard.html"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        # ── Role context ──
        role_context = get_role_context(request.user)
        is_admin = role_context.get("is_admin", False)
        is_reviewer = role_context.get("is_reviewer", False)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_superuser = request.user.is_superuser
        is_privileged = is_admin or is_reviewer or is_superuser

        # ── Zone / Site mappings ──
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # ── GET params ──
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else "All Zones"
        selected_site_name = sites.get(site_id_int, "") if site_id_int else "All Sites"

        # ── Role string (same pattern as specific form) ──
        role = "privileged" if is_privileged else (
            "zonal_lab" if is_zonal_lab else "default"
        )

        # ── Fetch missing form data ──
        missing_data = get_missing_forms_dq(
            request.user,
            zone_id_int,
            site_id_int,
            role=role,
        )

        # ── Update context ──
        context.update({
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

            **missing_data  # Inject totals directly (same as DQ)
        })

        return context
