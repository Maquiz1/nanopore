from django.views import View
from django.shortcuts import render
from django.apps import apps

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

from reports.services.zonal_dq_counts import get_zonal_dq_counts
from reports.services.zonal_problem_lists import get_zonal_problem_lists

class ZonalDataQualityReportView(View):
    template_name = "reports/data_quality/laboratory/zonal/data_zonal_quality_report.html"

    def get(self, request, *args, **kwargs):
        Zonal = apps.get_model("nanopore", "ZonalLaboratory")

        qs = Zonal.objects.select_related(
            "screening","screening__site","screening__site__district__region__zone"
        ).order_by(
            "screening__site__district__region__name","screening__site__name","screening__pid"
        )
        # qs = Zonal.objects.select_related(
        #     "screening",
        #     "screening__site",
        #     "screening__site__district__region__zone",
        # ).order_by(
        #     "screening__site__district__region__name",
        #     "screening__site__name",
        #     "screening__pid"
        # )

        role_context = get_role_context(request.user)
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        qs = filter_queryset_by_user_role(request.user, qs, site_field="screening__site")

        zone_id = int(request.GET.get("zone") or 0) or None
        site_id = int(request.GET.get("site") or 0) or None

        if zone_id:
            qs = qs.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(screening__site_id=site_id)

        # Get aggregated counts
        counts_data = get_zonal_dq_counts(qs)
        duplicate_lab_numbers = counts_data["duplicate_lab_numbers"]
        stats = counts_data["stats"]
        total_issues = counts_data["total_issues"]

        # Get problem lists (uses default ZONAL_DQ_FIELD_MAPPING from service)
        problem_lists = get_zonal_problem_lists(qs, duplicate_lab_numbers)

        context = {
            "total_records": qs.count(),
            "zones": zones,
            "sites": sites,
            "selected_zone_name": zones.get(zone_id, "") if zone_id else "",
            "selected_site_name": sites.get(site_id, "") if site_id else "",
            "is_admin": role_context.get("is_admin", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_full_access": role_context.get("is_admin", False) or request.user.is_superuser,
            "stats": stats,
            **{f"count_{k}": v for k, v in stats.items()},
            "total_issues": total_issues,
            **problem_lists
        }

        return render(request, self.template_name, context)
