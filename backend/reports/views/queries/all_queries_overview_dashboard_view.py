from django.views.generic import TemplateView
from django.apps import apps
from utils.roles import get_role_context
from utils.permissions import filter_queryset_by_user_role

class AllOverviewQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/all_queries_overview_dashboard.html"

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)

    #     # ── Role context
    #     role_context = get_role_context(self.request.user)
    #     is_zonal_lab = role_context.get("is_zonal_lab", False)
    #     is_admin     = role_context.get("is_admin", False)
    #     is_reviewer  = role_context.get("is_reviewer", False)
    #     is_superuser = self.request.user.is_superuser
    #     is_privileged = is_admin or is_reviewer

    #     # ── Prepare zone and site mappings
    #     zones = {z.id: z.name for z in role_context.get("zones", [])}
    #     sites = {s.id: s.name for s in role_context.get("sites", [])}

    #     # ── Get filters from GET
    #     zone_id = self.request.GET.get("zone")
    #     site_id = self.request.GET.get("site")
    #     zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
    #     site_id_int = int(site_id) if site_id and site_id.isdigit() else None

    #     selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else ""
    #     selected_site_name = sites.get(site_id_int, "") if site_id_int else ""

    #     # ── Base queryset: all ZonalLaboratory entries
    #     ZonalLab = apps.get_model("nanopore", "ZonalLaboratory")
    #     qs = ZonalLab.objects.select_related("screening", "screening__site", "screening__site__district", "screening__site__district__region", "screening__site__district__region__zone")

    #     # ── Apply role-based filtering first
    #     qs = filter_queryset_by_user_role(self.request.user, qs)

    #     # ── Apply Zone / Site filters
    #     if zone_id_int and zone_id_int in zones:
    #         qs = qs.filter(screening__site__district__region__zone_id=zone_id_int)
    #     if site_id_int and site_id_int in sites:
    #         qs = qs.filter(screening__site_id=site_id_int)

    #     # ── Calculate counts for dashboard cards
    #     total_issues = qs.count()

    #     # Example for missing forms count — adjust logic as needed
    #     forms_missing_count = qs.filter(
    #         screening__enrollmentform__isnull=True
    #     ).count()

    #     # Example for specific queries count — adjust logic as needed
    #     specific_queries_count = qs.filter(
    #         screening__has_queries=True  # Replace with your actual field
    #     ).count()

    #     # ── Update context
    #     context.update({
    #         "is_admin": is_admin,
    #         "is_reviewer": is_reviewer,
    #         "is_zonal_lab": is_zonal_lab,
    #         "is_privileged": is_privileged,

    #         "zones": zones,
    #         "sites": sites,
    #         "selected_zone": zone_id or "",
    #         "selected_site": site_id or "",
    #         "selected_zone_name": selected_zone_name,
    #         "selected_site_name": selected_site_name,

    #         "total_issues": total_issues,
    #         "forms_report_total": {"total_form_missing": forms_missing_count},
    #         "specific_queries_total": specific_queries_count,
    #     })

    #     return context
