# reports/views/queries/laboratory/zonal/data_zonal_quality_view.py

from django.views import View
from django.shortcuts import render
from django.apps import apps

from reports.services.zonal_dq import get_zonal_dq

from utils.roles import get_role_context

class ZonalDataQualityView(View):

    template_name = "reports/data_quality/laboratory/zonal/data_zonal_quality_report.html"

    def get(self, request, *args, **kwargs):

        # Get model dynamically
        Zonal = apps.get_model("nanopore", "ZonalLaboratory")
        
        role_context = get_role_context(request.user)

        # Prepare zone and site mappings for template
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # Read filters from URL params
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id = int(site_id) if site_id and site_id.isdigit() else None

        # Validate filters against allowed zones/sites
        if zone_id and zone_id not in zones:
            zone_id = None

        if site_id and site_id not in sites:
            site_id = None

        qs, stats, total_issues, problem_lists = get_zonal_dq(
            request.user,
            Zonal,
            zone_id,
            site_id,
        )

        context = {
            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id,
            "selected_site": site_id,
            "total_records": qs.count(),
            "stats": stats,
            **{f"count_{k}": v for k, v in stats.items()},
            "total_issues": total_issues,
            **problem_lists,
        }

        return render(request, self.template_name, context)
