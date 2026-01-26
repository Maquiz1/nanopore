from django.views import View
from django.shortcuts import render
from django.apps import apps
from django.utils import timezone

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class RegimenDataQualityReportView(View):
    """Data Quality Report for Regimen Changes (role-aware)."""

    template_name = "reports/data_quality/regimens/data_regimen_quality_report.html"

    def get(self, request, *args, **kwargs):
        RegimenChanges = apps.get_model('nanopore', 'RegimenChanges')

        # --- Base QuerySet ---
        regimens = RegimenChanges.objects.select_related(
            'screening',
            'screening__site',
            'screening__site__district__region__zone',
        ).order_by(
            'screening__site__district__region__zone__name',
            'screening__site__name',
            'screening__pid',
        )

        # --- Role-Based Filtering ---
        regimens = filter_queryset_by_user_role(request.user, regimens, site_field="screening__site")

        # --- Optional Filters ---
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        if zone_id:
            regimens = regimens.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            regimens = regimens.filter(screening__site_id=site_id)

        total_regimens = regimens.count()

        # --- Required fields for completeness ---
        required_fields = ["date", "drug", "changes", "reason"]

        # --- Helper to serialize record for template ---
        def serialize_regimen(r):
            zone = getattr(r.screening.site.district.region.zone, "name", "") if r.screening and r.screening.site else ""
            site = getattr(r.screening.site, "name", "") if r.screening and r.screening.site else ""
            missing_fields = [f for f in required_fields if not getattr(r, f)]
            return {
                "pid": getattr(r.screening, "pid", ""),
                "zone": zone,
                "site": site,
                "date": r.date,
                "drug": r.drug,
                "changes": getattr(r.changes, "name", "") if r.changes else "",
                "reason": getattr(r.reason, "name", "") if r.reason else "",
                "specify": r.specify,
                "missing_fields": missing_fields,
            }

        # --- Identify incomplete and complete records ---
        incomplete_regimens = [serialize_regimen(r) for r in regimens if any(not getattr(r, f) for f in required_fields)]
        complete_regimens = [serialize_regimen(r) for r in regimens if all(getattr(r, f) for f in required_fields)]

        # --- Role Context ---
        role_context = get_role_context(request.user)
        is_admin = role_context.get("is_admin", False)
        is_reviewer = role_context.get("is_reviewer", False)
        is_zonal_lab = role_context.get("is_zonal_lab", False)

        # --- Context ---
        context = {
            "total_regimens": total_regimens,
            "incomplete_regimens": incomplete_regimens,
            "complete_regimens": complete_regimens,
            "report_total": len(incomplete_regimens),
            "zones": {z.id: z.name for z in role_context["zones"]},
            "sites": {s.id: s.name for s in role_context["sites"]},
            "is_admin": is_admin,
            "is_reviewer": is_reviewer,
            "is_zonal_lab": is_zonal_lab,
            "is_national_lab": role_context.get("is_national_lab", False),
            "is_site_only": role_context.get("is_site_only", False),
            "report_date": timezone.now(),
        }

        return render(request, self.template_name, context)
