# reports/views/queries/regimen/data_regimen_quality_view.py
from reports.services.regimen_dq import get_regimen_queryset, get_regimen_dq

from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class RegimenDataQualityReportView(View):
    template_name = "reports/data_quality/regimens/data_regimen_quality_report.html"

    def get(self, request, *args, **kwargs):
        qs = get_regimen_queryset(request.user, zone_id_int, site_id_int)

        issues, totals = get_regimen_dq(qs)

        context.update({
            "missing_date": [serialize_regimen(r) for r in issues["missing_date"][:100]],
            "missing_drug": [serialize_regimen(r) for r in issues["missing_drug"][:100]],
            "missing_changes": [serialize_regimen(r) for r in issues["missing_changes"][:100]],
            "missing_reason": [serialize_regimen(r) for r in issues["missing_reason"][:100]],
            "missing_specify_when_other": [serialize_regimen(r) for r in issues["missing_specify"][:100]],
        })

        context.update(totals)
