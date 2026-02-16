# reports/views/queries/regimen/data_regimen_quality_view.py
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
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

        regimens = (
            RegimenChanges.objects
            .select_related(
                "screening",
                "screening__site",
                "screening__site__district",
                "screening__site__district__region",
                "screening__site__district__region__zone",
                "changes",
                "reason",
            )
            .order_by(
                "screening__site__district__region__zone__name",
                "screening__site__name",
                "screening__pid",
                "-date",
            )
        )

        role_context = get_role_context(request.user)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_admin     = role_context.get("is_admin", False)
        is_reviewer  = role_context.get("is_reviewer", False)
        is_superuser = request.user.is_superuser
        is_full_access = is_admin or is_superuser
        is_privileged = is_admin or is_reviewer
        
        # ──────────────────────────────────────────────
        # Zones and Sites for filters
        # ──────────────────────────────────────────────
        
        # 🔐 role-based access
        regimens = filter_queryset_by_user_role(
            request.user,
            regimens,
            site_field="screening__site"
        )

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
            regimens = regimens.filter(screening__site__district__region__zone_id=zone_id_int)

        if site_id_int and site_id_int in sites:
            regimens = regimens.filter(screening__site_id=site_id_int)

        total_regimens = regimens.count()

        # ──────────────────────────────────────────────
        # Safe serializer
        # ──────────────────────────────────────────────
        def serialize_regimen(r):
            screening = r.screening
            site = getattr(screening, "site", None)
            district = getattr(site, "district", None)
            region = getattr(district, "region", None)
            zone = getattr(region, "zone", None)

            return {
                "id": r.id,
                "pid": getattr(screening, "pid", ""),
                "zone_name": getattr(zone, "name", ""),
                "site_name": getattr(site, "name", ""),
                "date": r.date,
                "drug": r.drug or "",
                "change_type": getattr(r.changes, "name", ""),
                "reason": getattr(r.reason, "name", ""),
                "specify": r.specify or "",
            }

        # ──────────────────────────────────────────────
        # Missing field checks
        # ──────────────────────────────────────────────
        missing_date_qs = regimens.filter(date__isnull=True)

        missing_drug_qs = regimens.filter(
            Q(drug__isnull=True) | Q(drug__exact="")
        )

        missing_changes_qs = regimens.filter(changes__isnull=True)

        missing_reason_qs = regimens.filter(reason__isnull=True)

        # reason = Other (96)
        reason_is_96_q = (
            Q(reason__value=96) |
            Q(reason__name__iexact="96") |
            Q(reason__name__iexact="other")
        )

        missing_specify_qs = regimens.filter(
            reason_is_96_q
        ).filter(
            Q(specify__isnull=True) | Q(specify__exact="")
        )

        context = {
            "report_title": "Regimen Changes Data Quality Report",
            "report_date": timezone.now(),
            "total_regimens": total_regimens,

            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),

            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,

            # preview lists
            "missing_date": [serialize_regimen(r) for r in missing_date_qs[:100]],
            "missing_drug": [serialize_regimen(r) for r in missing_drug_qs[:100]],
            "missing_changes": [serialize_regimen(r) for r in missing_changes_qs[:100]],
            "missing_reason": [serialize_regimen(r) for r in missing_reason_qs[:100]],
            "missing_specify_when_other": [
                serialize_regimen(r) for r in missing_specify_qs[:100]
            ],
        }

        # counts
        context.update({
            "count_missing_date": missing_date_qs.count(),
            "count_missing_drug": missing_drug_qs.count(),
            "count_missing_changes": missing_changes_qs.count(),
            "count_missing_reason": missing_reason_qs.count(),
            "count_missing_specify_when_other": missing_specify_qs.count(),
        })

        # auto total
        context["regimen_report_total"] = sum(
            v for k, v in context.items()
            if k.startswith("count_missing_") and isinstance(v, int)
        )

        context["total_issues"] = context["regimen_report_total"]

        return render(request, self.template_name, context)
