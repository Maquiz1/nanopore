from django.views.generic import TemplateView
from django.apps import apps
from django.db.models import Exists, OuterRef
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

class MissingFormQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/missing_form_queries_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request  # ✅ Use self.request in TemplateView

        # ── Role context ──
        role_context = get_role_context(request.user)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_admin     = role_context.get("is_admin", False)
        is_reviewer  = role_context.get("is_reviewer", False)
        is_superuser = request.user.is_superuser
        is_privileged = is_admin or is_reviewer

        # ── Zone / Site mappings ──
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # ── GET params ──
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else ""
        selected_site_name = sites.get(site_id_int, "") if site_id_int else ""

        # ── Models ──
        Screening        = apps.get_model("nanopore", "Screening")
        ClinicLaboratory = apps.get_model("nanopore", "ClinicLaboratory")
        Diagnosis        = apps.get_model("nanopore", "Diagnosis")
        RegimenChanges   = apps.get_model("nanopore", "RegimenChanges")
        ZonalLaboratory  = apps.get_model("nanopore", "ZonalLaboratory")

        # ── Base queryset filtered by user role ──
        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "enrollment",
            "clinic_laboratory",
            "diagnosis",
            "zonal_laboratory",
        ).prefetch_related("regimen_changes")

        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        eligible_screenings = screenings.filter(eligible=True)

        # ── Apply zone/site filters ──
        if zone_id_int:
            eligible_screenings = eligible_screenings.filter(site__district__region__zone_id=zone_id_int)
        if site_id_int:
            eligible_screenings = eligible_screenings.filter(site_id=site_id_int)

        # ── Compute counts ──
        missing_enrollment_count = eligible_screenings.filter(enrollment__isnull=True).count()
        missing_clinic_count = eligible_screenings.filter(clinic_laboratory__isnull=True).count()
        missing_diagnosis_count = eligible_screenings.filter(diagnosis__isnull=True).count()
        has_regimen_changes_subquery = RegimenChanges.objects.filter(screening=OuterRef("pk"))
        missing_regimen_count = eligible_screenings.filter(
            ~Exists(has_regimen_changes_subquery),
            diagnosis__isnull=False,
            diagnosis__regimen_changed__name="Yes",
        ).distinct().count()
        missing_zonal_count = 0
        if is_privileged or is_zonal_lab:
            missing_zonal_count = eligible_screenings.filter(
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2,3,4,5,6],
                zonal_laboratory__isnull=True
            ).count()

        # ── Total based on role ──
        if is_privileged:
            total_form_missing = (missing_enrollment_count + missing_clinic_count +
                                  missing_diagnosis_count + missing_regimen_count + missing_zonal_count)
        elif is_zonal_lab:
            total_form_missing = missing_zonal_count
        else:
            total_form_missing = (missing_enrollment_count + missing_clinic_count +
                                  missing_diagnosis_count + missing_regimen_count)

        # ── Add all to context ──
        context.update({
            "is_admin": is_admin,
            "is_reviewer": is_reviewer,
            "is_zonal_lab": is_zonal_lab,
            "is_privileged": is_privileged,
            
            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,

            "missing_enrollment_count": missing_enrollment_count,
            "missing_clinic_count": missing_clinic_count,
            "missing_diagnosis_count": missing_diagnosis_count,
            "missing_regimen_count": missing_regimen_count,
            "missing_zonal_count": missing_zonal_count,
            "total_form_missing": total_form_missing,
        })

        return context
