# reports/views/queries/laboratory/zonal/data_zonal_quality_view.py

from django.views import View
from django.shortcuts import render
from django.apps import apps

from reports.services.zonal_dq import get_zonal_dq


class EdcsTBLISDataQualityView(View):

    template_name = "reports/data_quality/laboratory/edcs_tblis/data_edcs_tblis_quality_report.html"

    def get(self, request, *args, **kwargs):

        # Get model dynamically
        Zonal = apps.get_model("nanopore", "EdcsTblisZonal")

        # Read filters from URL params (?zone_id=1&site_id=2)
        zone_id = request.GET.get("zone_id")
        site_id = request.GET.get("site_id")

        qs, stats, total_issues, problem_lists = get_zonal_dq(
            request.user,
            Zonal,
            zone_id,
            site_id,
        )

        context = {
            "total_records": qs.count(),
            "stats": stats,
            **{f"count_{k}": v for k, v in stats.items()},
            "total_issues": total_issues,
            **problem_lists,
        }

        return render(request, self.template_name, context)
