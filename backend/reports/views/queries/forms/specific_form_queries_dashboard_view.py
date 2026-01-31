# reports/views/mentorships/specific_form_queries_dashboard_view.py
from django.views.generic import TemplateView
from utils.roles import get_role_context
from reports.services.screening_dq_counts import get_screening_dq_counts
from reports.services.enrollment_dq_counts import get_enrollment_dq_counts
from reports.services.regimen_dq_counts import get_regimen_dq_counts
from reports.services.diagnosis_dq_counts import get_diagnosis_dq_counts
from reports.services.clinic_dq_counts import get_clinic_dq_counts
from reports.services.zonal_dq_counts import get_zonal_dq_counts

class SpecificFormQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/specific_form_queries_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        # ── Get zone/site IDs safely ──
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        # ── Fetch counts from service functions ──
        screening = get_screening_dq_counts(request.user, zone_id_int, site_id_int)
        enrollment = get_enrollment_dq_counts(request.user, zone_id_int, site_id_int)
        regimen = get_regimen_dq_counts(request.user, zone_id_int, site_id_int)
        diagnosis = get_diagnosis_dq_counts(request.user, zone_id_int, site_id_int)
        clinic = get_clinic_dq_counts(request.user, zone_id_int, site_id_int)
        zonal = get_zonal_dq_counts(request.user, zone_id_int, site_id_int)

        # ── Update totals in context ──
        total_screening = screening.get("total", 0)
        total_enrollment = enrollment.get("total", 0)
        total_regimen = regimen.get("total", 0)
        total_diagnosis = diagnosis.get("total", 0)
        total_clinic = clinic.get("total", 0)
        total_zonal = zonal.get("total", 0)

        context.update({
            "screening_report_total": total_screening,
            "enrollment_report_total": total_enrollment,
            "regimen_report_total": total_regimen,
            "diagnosis_report_total": total_diagnosis,
            "clinic_report_total": total_clinic,
            "zonal_report_total": total_zonal,
            "specific_queries_total": (
                total_screening
                + total_enrollment
                + total_regimen
                + total_diagnosis
                + total_clinic
                + total_zonal
            ),
        })

        # ── Role context ──
        role_context = get_role_context(request.user)
        context.update({
            "is_admin": role_context.get("is_admin", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_privileged": role_context.get("is_admin", False) or role_context.get("is_reviewer", False),
            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
        })

        return context
