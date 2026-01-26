# reports/views/mentorships/forms_data_quality_report_view.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class FormsDataQualityReportView(View):
    """
    Detailed report: Eligible screenings missing the Enrollment form.

    Shows:
    - list of problematic records
    - summary counts
    - filter options (zone/site)

    Uses exactly the same filtering & scoping logic as the context processor
    `forms_report_total` so numbers stay consistent with the dashboard.
    """

    template_name = "reports/data_quality/forms/form_missing_queries_dashboard.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model("nanopore", "Screening")

        # ────────────────────────────────────────────────────────────────
        # Base queryset — mirror the context processor as closely as possible
        # ────────────────────────────────────────────────────────────────
        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "sex",
            "enrollment",
            "clinic_laboratory",
            "diagnosis",
            "zonal_laboratory",
        ).prefetch_related(
            "regimen_changes",           # for possible future extension
        ).order_by(
            "site__district__region__name",
            "site__name",
            "pid",
        )

        # Apply the same permission scoping
        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        # ────────────────────────────────────────────────────────────────
        # Optional GET filters (zone / site) — keep these
        # ────────────────────────────────────────────────────────────────
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        if zone_id:
            screenings = screenings.filter(site__district__region__zone_id=zone_id)
        if site_id:
            screenings = screenings.filter(site_id=site_id)

        # Total eligible screenings after scoping + filters
        total_screenings = screenings.filter(eligible=True).count()

        # ────────────────────────────────────────────────────────────────
        # The records we care about — same logic as context processor
        # ────────────────────────────────────────────────────────────────
        missing_enrollment_qs = screenings.filter(
            eligible=True,
            enrollment__isnull=True
        )

        report_total = missing_enrollment_qs.count()  # should match forms_report_total.missing_enrollment_count

        # ────────────────────────────────────────────────────────────────
        # Prepare safe, minimal dicts for the template
        # ────────────────────────────────────────────────────────────────
        def serialize_screening(s):
            zone = getattr(
                getattr(
                    getattr(
                        getattr(s, "site", None), "district", None
                    ), "region", None
                ), "zone", None
            )
            return {
                "id": s.id,
                "pid": getattr(s, "pid", ""),
                "screening_date": getattr(s, "screening_date", None),
                "zone_name": zone.name if zone else "",
                "site_name": getattr(getattr(s, "site", None), "name", ""),
                "sex": getattr(getattr(s, "sex", None), "name", ""),
                "age": getattr(s, "age", None),
            }

        missing_enrollment_records = [
            serialize_screening(s) for s in missing_enrollment_qs
        ]

        # ────────────────────────────────────────────────────────────────
        # Role context + filter dropdown choices
        # ────────────────────────────────────────────────────────────────
        role_context = get_role_context(request.user)

        context = {
            # Summary numbers — should align with dashboard
            "total_screenings": total_screenings,
            "report_total": report_total,                        # ← must == forms_report_total.missing_enrollment_count
            "missing_enrollment_records": missing_enrollment_records,  # renamed for clarity

            # Current filter values (for <select> selected="")
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",

            # Role-based flags (conditional rendering in template)
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_superuser": request.user.is_superuser,

            # Dropdown choices — passed from role context
            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},
            
            # Metadata
            "report_date": timezone.now(),
            "report_title": "Forms Data Quality – Missing Enrollments",
            "page_description": "Eligible participants screened but without linked enrollment form",
        }

        return render(request, self.template_name, context)