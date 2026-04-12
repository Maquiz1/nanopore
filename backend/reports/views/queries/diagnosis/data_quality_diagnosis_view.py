from django.views import View
from django.shortcuts import render

from reports.services.diagnosis_dq import (
    get_diagnosis_queryset,
    get_diagnosis_dq,
)
from utils.roles import get_role_context


class DiagnosisDataQualityView(View):

    template_name = (
        "reports/data_quality/diagnosis/data_diagnosis_quality_report.html"
    )

    def get(self, request, *args, **kwargs):

        role_context = get_role_context(request.user)

        # Prepare zone and site mappings for template
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # Read filters from URL params
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id = int(site_id) if site_id and site_id.isdigit() else None
        
        # zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        # site_id_int = int(site_id) if site_id and site_id.isdigit() else None
        selected_zone_name = zones.get(zone_id, "") if zone_id else "All Zones"
        selected_site_name = sites.get(site_id, "") if site_id else "All Sites"

        # Validate filters against allowed zones/sites
        if zone_id and zone_id not in zones:
            zone_id = None

        if site_id and site_id not in sites:
            site_id = None

        # Build filtered queryset
        qs = get_diagnosis_queryset(
            request.user,
            zone_id,
            site_id,
        )

        # Run DQ checks
        problem_lists, stats = get_diagnosis_dq(qs)

        total_issues = stats.get("diagnosis_report_total", 0)

        context = {
            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id,
            "selected_site": site_id,
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,
            "total_records": qs.count(),
            "stats": stats,
            **stats,               # gives count_missing_...
            "total_issues": total_issues,
            "context_diagnosis_report_total": total_issues,
            **problem_lists,       # gives missing_tb_diagnosis etc (querysets)
        }

        return render(request, self.template_name, context)
