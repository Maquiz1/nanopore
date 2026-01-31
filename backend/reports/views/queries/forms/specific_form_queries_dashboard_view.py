from django.views.generic import TemplateView
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

class SpecificFormQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/specific_form_queries_dashboard.html"
    
    def get(self, request, *args, **kwargs):
            context = super().get_context_data(**kwargs)

            # ── Your role logic (you probably already have this somewhere) ──
            role_context = get_role_context(request.user)
            is_zonal_lab = role_context.get("is_zonal_lab", False)
            is_admin     = role_context.get("is_admin", False)
            is_reviewer  = role_context.get("is_reviewer", False)
            is_superuser = request.user.is_superuser
            is_full_access = is_admin or is_superuser
            is_privileged = is_admin or is_reviewer
            
            
            # Prepare zone and site mappings for template
            zones = {z.id: z.name for z in role_context.get("zones", [])}
            sites = {s.id: s.name for s in role_context.get("sites", [])}

            # After getting zone_id and site_id from GET
            zone_id = request.GET.get("zone")
            site_id = request.GET.get("site")

            # Convert to int if possible
            zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
            site_id_int = int(site_id) if site_id and site_id.isdigit() else None

            # Resolve names for template
            selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else ""
            selected_site_name = sites.get(site_id_int, "") if site_id_int else ""

            # Apply filters
            if zone_id_int and zone_id_int in zones:
                qs = qs.filter(screening__site__district__region__zone_id=zone_id_int)

            if site_id_int and site_id_int in sites:
                qs = qs.filter(screening__site_id=site_id_int)

            # ── This is where you add the flags to the template context ──
            context.update({
                'is_admin': is_admin,
                'is_reviewer': is_reviewer,
                'is_zonal_lab': is_zonal_lab,
                'is_privileged': is_privileged,
                
                "zones": zones,
                "sites": sites,
                "selected_zone": zone_id or "",
                "selected_site": site_id or "",
                "selected_zone_name": selected_zone_name,
                "selected_site_name": selected_site_name,
            })

            # Probably already adding forms_report_total via context processor
            # If not — add it here too:
            # context['forms_report_total'] = forms_report_total(self.request)['forms_report_total']

            return context