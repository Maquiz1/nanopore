# reports/views/mentorships/missing_form_queries_view.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Exists, OuterRef

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class MissingFormDetailsQueriesView(View):
    """
    Detailed forms data quality report.

    This view mirrors the logic in utils.context_processors.forms_report_total
    but returns both:
      - summary counts (keys matching the context processor)
      - lists of problematic records (serialized minimal dicts)

    The lists are limited to the full queryset (no hard limit here) so templates
    can paginate or slice if needed. All queries are scoped by the same
    permission helper so numbers remain consistent.
    """

    template_name = "reports/data_quality/forms/missing_form_details_queries.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model("nanopore", "Screening")
        Diagnosis = apps.get_model("nanopore", "Diagnosis")
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")
        ClinicLaboratory = apps.get_model("nanopore", "ClinicLaboratory")
        ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")

        # Base queryset — mirror the context processor as closely as possible
        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "sex",
            "enrollment",
            "clinic_laboratory",
            "diagnosis",
            "zonal_laboratory",
        ).prefetch_related(
            "regimen_changes",
        ).order_by(
            "site__district__region__name",
            "site__name",
            "pid",
        )

        # Apply the same permission scoping
        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        # Optional GET filters (zone / site)
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        if zone_id:
            screenings = screenings.filter(site__district__region__zone_id=zone_id)
        if site_id:
            screenings = screenings.filter(site_id=site_id)

        # Only eligible screenings are considered
        eligible_screenings = screenings.filter(eligible=True)

        # 1) Missing Enrollment
        missing_enrollment_qs = eligible_screenings.filter(enrollment__isnull=True)
        missing_enrollment_count = missing_enrollment_qs.count()

        # 2) Missing Clinic Laboratory
        missing_clinic_qs = eligible_screenings.filter(clinic_laboratory__isnull=True)
        missing_clinic_count = missing_clinic_qs.count()

        # 3) Missing Diagnosis
        missing_diagnosis_qs = eligible_screenings.filter(diagnosis__isnull=True)
        missing_diagnosis_count = missing_diagnosis_qs.count()

        # 4) Missing Zonal Laboratory
        missing_zonal_qs = eligible_screenings.filter(zonal_laboratory__isnull=True)
        missing_zonal_count = missing_zonal_qs.count()

        # 5) Missing Regimen Changes
        # Only screenings where diagnosis.regimen_changed == "Yes" and no RegimenChanges exist
        has_regimen_changes_subquery = RegimenChanges.objects.filter(screening=OuterRef("pk"))
        missing_regimen_qs = eligible_screenings.filter(
            ~Exists(has_regimen_changes_subquery),
            diagnosis__isnull=False,
            diagnosis__regimen_changed__name="Yes",
        ).distinct()
        missing_regimen_count = missing_regimen_qs.count()

        # Total missing forms (sum of the above counts)
        total_form_missing = (
            missing_enrollment_count
            + missing_clinic_count
            + missing_diagnosis_count
            + missing_regimen_count
            + missing_zonal_count
        )

        # --- Serialization helpers ---
        def _serialize_screening(s):
            zone = getattr(
                getattr(
                    getattr(getattr(s, "site", None), "district", None),
                    "region",
                    None,
                ),
                "zone",
                None,
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

        # Prepare lists (serialized)
        missing_enrollment_records = [_serialize_screening(s) for s in missing_enrollment_qs]
        missing_clinic_records = [_serialize_screening(s) for s in missing_clinic_qs]
        missing_diagnosis_records = [_serialize_screening(s) for s in missing_diagnosis_qs]
        missing_zonal_records = [_serialize_screening(s) for s in missing_zonal_qs]
        missing_regimen_records = [_serialize_screening(s) for s in missing_regimen_qs]

        # Role context + filter dropdown choices
        role_context = get_role_context(request.user)

        context = {
            # Metadata
            "report_date": timezone.now(),
            "report_title": "Forms Data Quality – Missing Forms",

            # Counts (keys aligned with context processor)
            "total_form_missing": total_form_missing,
            "missing_enrollment_count": missing_enrollment_count,
            "missing_clinic_count": missing_clinic_count,
            "missing_diagnosis_count": missing_diagnosis_count,
            "missing_regimen_count": missing_regimen_count,
            "missing_zonal_count": missing_zonal_count,

            # Lists (serialized) for templates to render
            "missing_enrollment_records": missing_enrollment_records,
            "missing_clinic_records": missing_clinic_records,
            "missing_diagnosis_records": missing_diagnosis_records,
            "missing_regimen_records": missing_regimen_records,
            "missing_zonal_records": missing_zonal_records,

            # Totals and filters
            "total_screenings": eligible_screenings.count(),
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",

            # Role flags and dropdown choices
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_superuser": request.user.is_superuser,
            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},

            # Page info
            "page_description": "Eligible participants screened but missing downstream forms",
        }

        return render(request, self.template_name, context)
