from django.views import View
from django.shortcuts import render

from reports.services.screening_dq import (
    get_screening_queryset,
    get_screening_dq,
)


class ScreeningDataQualityView(View):

    template_name = "reports/data_quality/screenings/data_screening_quality_report.html"

    def get(self, request, *args, **kwargs):

        # Read filters from URL params
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id = int(site_id) if site_id and site_id.isdigit() else None

        # Build filtered queryset
        qs = get_screening_queryset(
            request.user,
            zone_id,
            site_id,
        )

        # Run DQ checks
        problem_lists, stats = get_screening_dq(qs)

        total_issues = stats.get("screening_report_total", 0)

        context = {
            "total_records": qs.count(),
            "stats": stats,
            **stats,               # gives count_missing_...
            "total_issues": total_issues,
            **problem_lists,       # gives missing_pid1 etc (querysets)
        }

        return render(request, self.template_name, context)
