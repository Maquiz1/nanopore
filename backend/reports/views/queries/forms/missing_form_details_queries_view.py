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
    Detailed view of missing forms.
    - Shows summary counts for all forms (role-aware)
    - Shows detailed list only for the requested form_type
    """

    template_name = "reports/data_quality/forms/missing_form_details_queries.html"

    FORM_ID_MAP = {
        1: "enrollment",
        2: "clinic",
        3: "diagnosis",
        4: "regimen",
        5: "zonal",
    }

    def get(self, request, *args, **kwargs):
        # ── 1. Determine requested form_type (URL has highest priority) ──
        form_type = kwargs.get("form_type")                     # from URL: /.../<str:form_type>/

        # Fallback: ?form_type=... GET param (if URL param missing)
        if not form_type:
            form_type = request.GET.get("form_type")

        # Fallback: numeric ?form_id= or /<int:form_id>/ (old style)
        form_id = kwargs.get("form_id")
        if form_id:
            form_type = self.FORM_ID_MAP.get(int(form_id), form_type)

        # Final fallback only if nothing is provided
        form_type = form_type or "enrollment"

        # Debug (remove in production)
        # print(f"DEBUG: Resolved form_type = {form_type!r}")

        # ── 2. Role context ───────────────────────────────────────────────
        role_context = get_role_context(request.user)
        is_admin     = role_context.get("is_admin", False)
        is_reviewer  = role_context.get("is_reviewer", False)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_privileged = is_admin or is_reviewer

        # ── 3. Base queryset ──────────────────────────────────────────────
        Screening = apps.get_model("nanopore", "Screening")
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

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

        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        # Optional filters (zone/site)
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        if zone_id:
            screenings = screenings.filter(site__district__region__zone_id=zone_id)
        if site_id:
            screenings = screenings.filter(site_id=site_id)

        eligible_screenings = screenings.filter(eligible=True)

        # ── 4. Compute counts (role-aware) ────────────────────────────────
        missing_enrollment_count = eligible_screenings.filter(enrollment__isnull=True).count()
        missing_clinic_count     = eligible_screenings.filter(clinic_laboratory__isnull=True).count()
        missing_diagnosis_count  = eligible_screenings.filter(diagnosis__isnull=True).count()

        missing_zonal_count = 0
        if is_privileged or is_zonal_lab:
            missing_zonal_count = eligible_screenings.filter(
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
                zonal_laboratory__isnull=True
            ).count()

        has_regimen_changes_subquery = RegimenChanges.objects.filter(screening=OuterRef("pk"))
        missing_regimen_qs = eligible_screenings.filter(
            ~Exists(has_regimen_changes_subquery),
            diagnosis__isnull=False,
            diagnosis__regimen_changed__name="Yes",
        ).distinct()
        missing_regimen_count = missing_regimen_qs.count()

        # Total (role-aware)
        if is_privileged:
            total_form_missing = (
                missing_enrollment_count +
                missing_clinic_count +
                missing_diagnosis_count +
                missing_regimen_count +
                missing_zonal_count
            )
        elif is_zonal_lab:
            total_form_missing = missing_zonal_count
        else:
            total_form_missing = (
                missing_enrollment_count +
                missing_clinic_count +
                missing_diagnosis_count +
                missing_regimen_count
            )

        # ── 5. Prepare records only for the requested form_type ───────────
        missing_records = []
        selected_qs = None

        if form_type == "enrollment":
            selected_qs = eligible_screenings.filter(enrollment__isnull=True)
        elif form_type == "clinic":
            selected_qs = eligible_screenings.filter(clinic_laboratory__isnull=True)
        elif form_type == "diagnosis":
            selected_qs = eligible_screenings.filter(diagnosis__isnull=True)
        elif form_type == "zonal" and (is_privileged or is_zonal_lab):
            selected_qs = eligible_screenings.filter(
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
                zonal_laboratory__isnull=True
            )
        elif form_type == "regimen":
            selected_qs = missing_regimen_qs

        if selected_qs is not None:
            def _serialize_screening(s):
                zone = getattr(
                    getattr(
                        getattr(getattr(s, "site", None), "district", None),
                        "region", None,
                    ),
                    "zone", None,
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

            missing_records = [_serialize_screening(s) for s in selected_qs]

        # ── 6. Context ────────────────────────────────────────────────────
        context = {
            "report_date": timezone.now(),
            "report_title": "Forms Data Quality – Missing Forms Details",

            "total_form_missing": total_form_missing,
            "missing_enrollment_count": missing_enrollment_count,
            "missing_clinic_count": missing_clinic_count,
            "missing_diagnosis_count": missing_diagnosis_count,
            "missing_regimen_count": missing_regimen_count,
            "missing_zonal_count": missing_zonal_count,

            "missing_records": missing_records,
            "form_type": form_type,               # ← now correctly set from URL

            "total_screenings": eligible_screenings.count(),
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",

            "is_admin": is_admin,
            "is_reviewer": is_reviewer,
            "is_zonal_lab": is_zonal_lab,
            "is_privileged": is_privileged,
            "is_superuser": request.user.is_superuser,

            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},
        }

        return render(request, self.template_name, context)