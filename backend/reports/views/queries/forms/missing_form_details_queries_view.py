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
        # ── 1. Determine requested form_type ──
        form_type = kwargs.get("form_type") or request.GET.get("form_type")
        form_id = kwargs.get("form_id")
        if form_id:
            form_type = self.FORM_ID_MAP.get(int(form_id), form_type)
        form_type = form_type or "enrollment"

        # ── 2. Role context ──
        role_context = get_role_context(request.user)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_admin     = role_context.get("is_admin", False)
        is_reviewer  = role_context.get("is_reviewer", False)
        is_superuser = request.user.is_superuser
        is_privileged = is_admin or is_reviewer

        # ── 3. Base queryset ──
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
        ).prefetch_related("regimen_changes").order_by(
            "site__district__region__name",
            "site__name",
            "pid",
        )

        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        # ── 4. Zone / Site filters ──
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        if zone_id_int:
            screenings = screenings.filter(site__district__region__zone_id=zone_id_int)
        if site_id_int:
            screenings = screenings.filter(site_id=site_id_int)

        selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else ""
        selected_site_name = sites.get(site_id_int, "") if site_id_int else ""

        eligible_screenings = screenings.filter(eligible=True)

        # ── 5. Compute missing counts ──
        missing_enrollment_count = eligible_screenings.filter(enrollment__isnull=True).count()
        missing_clinic_count     = eligible_screenings.filter(clinic_laboratory__isnull=True).count()
        missing_diagnosis_count  = eligible_screenings.filter(diagnosis__isnull=True).count()

        has_regimen_changes_subquery = RegimenChanges.objects.filter(screening=OuterRef("pk"))
        missing_regimen_qs = eligible_screenings.filter(
            ~Exists(has_regimen_changes_subquery),
            diagnosis__isnull=False,
            diagnosis__regimen_changed__name="Yes",
        ).distinct()
        missing_regimen_count = missing_regimen_qs.count()

        missing_zonal_count = 0
        if is_privileged or is_zonal_lab:
            missing_zonal_count = eligible_screenings.filter(
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
                zonal_laboratory__isnull=True
            ).count()

        # ── 6. Total (role-aware) ──
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

        # ── 7. Select records for requested form_type ──
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

        missing_records = []
        if selected_qs:
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

        # ── 8. Render context ──
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
            "form_type": form_type,
            "total_screenings": eligible_screenings.count(),

            "is_admin": is_admin,
            "is_reviewer": is_reviewer,
            "is_zonal_lab": is_zonal_lab,
            "is_privileged": is_privileged,
            "is_superuser": is_superuser,

            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,
        }

        return render(request, self.template_name, context)

