# reports/views/laboratory/zonal/zonal_data_quality_report_view.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class ZonalDataQualityReportView(View):
    """
    Data quality report focused on linkage between Screening and ZonalLaboratory records,
    plus completeness of key ZonalLaboratory fields — role-aware with filtering.
    """
    template_name = "reports/data_quality/laboratory/zonal/data_zonal_quality_report.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model("nanopore", "Screening")
        ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")

        # ── Base queryset ─────────────────────────────────────────────────────
        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "zonal_laboratory",
            # Note: removed "zonal_laboratory__appearance" from select_related
            # because appearance is most likely NOT a ForeignKey
        ).order_by(
            "site__district__region__zone__name",
            "site__name",
            "pid",
        )

        # Role-based filtering
        screenings = filter_queryset_by_user_role(
            request.user,
            screenings,
            site_field="site"
        )

        # Optional zone/site filters
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        if zone_id:
            screenings = screenings.filter(site__district__region__zone_id=zone_id)
        if site_id:
            screenings = screenings.filter(site_id=site_id)

        total_records = screenings.count()

        # ── Serialization helper ──────────────────────────────────────────────
        def serialize_record(s):
            zl = getattr(s, "zonal_laboratory", None)
            site = getattr(s, "site", None)

            # Safe zone name extraction
            zone_name = ""
            if site:
                district = getattr(site, "district", None)
                if district:
                    region = getattr(district, "region", None)
                    if region:
                        zone = getattr(region, "zone", None)
                        if zone:
                            zone_name = getattr(zone, "name", "")

            # Appearance: most likely a CharField → just take the value directly
            appearance_value = ""
            if zl:
                appearance = getattr(zl, "appearance", None)
                if appearance:
                    # If it's a model instance → use .name, otherwise use the value
                    if hasattr(appearance, "name"):
                        appearance_value = appearance.name
                    else:
                        # CharField, string, etc.
                        appearance_value = str(appearance)

            return {
                "id": s.id,
                "pid": getattr(s, "pid", ""),
                "screening_date": getattr(s, "screening_date", None),
                "zone_name": zone_name,
                "site_name": getattr(site, "name", ""),
                "zonal_lab_id": zl.id if zl else None,
                "date_sputum_received": getattr(zl, "date_sputum_received", None),
                "unique_lab_no": getattr(zl, "unique_lab_no", ""),
                "appearance": appearance_value,
                "sample_volume": getattr(zl, "sample_volume", None),
                "has_zonal_lab": bool(zl),
            }

        # ── ZonalLaboratory field-level checks (only when form exists) ────────
        with_zonal = screenings.filter(zonal_laboratory__isnull=False)

        missing_date_sputum_received_qs = with_zonal.filter(
            zonal_laboratory__date_sputum_received__isnull=True
        )
        missing_appearance_qs = with_zonal.filter(
            zonal_laboratory__appearance__isnull=True
        )
        missing_sample_volume_qs = with_zonal.filter(
            zonal_laboratory__sample_volume__isnull=True
        )
        missing_unique_lab_no_qs = with_zonal.filter(
            zonal_laboratory__unique_lab_no__isnull=True
        )

        # ── Role context & main context ───────────────────────────────────────
        role_context = get_role_context(request.user)

        context = {
            "total_records": total_records,
            "report_date": timezone.now(),
            "report_title": "Zonal Laboratory Linkage & Data Quality Report",
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_national_lab": role_context.get("is_national_lab", False),
            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",

            # ── Problem lists (limited to 100) ────────────────────────────────
            "missing_date_sputum_received": [serialize_record(s) for s in missing_date_sputum_received_qs[:100]],
            "missing_appearance": [serialize_record(s) for s in missing_appearance_qs[:100]],
            "missing_sample_volume": [serialize_record(s) for s in missing_sample_volume_qs[:100]],
            "missing_unique_lab_no": [serialize_record(s) for s in missing_unique_lab_no_qs[:100]],
        }

        # ── Counts (dynamic generation) ───────────────────────────────────────
        count_keys = [
            "missing_date_sputum_received",
            "missing_appearance",
            "missing_sample_volume",
            "missing_unique_lab_no",
        ]

        for key in count_keys:
            qs_name = f"{key}_qs"
            if qs_name in locals():
                context[f"count_{key}"] = locals()[qs_name].count()

        # ── Total issues ──────────────────────────────────────────────────────
        context["total_issues"] = sum(
            context.get(f"count_{key}", 0) for key in count_keys
        )

        return render(request, self.template_name, context)