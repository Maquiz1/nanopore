# # reports/views/specific_form_queries_dashboard.py

# from django.views.generic import TemplateView
# from utils.roles import get_role_context
# from reports.services.specific_form_queries_dq_counts import get_specific_form_dq_counts

# class SpecificFormQueriesDashboardView(TemplateView):
#     template_name = (
#         "reports/data_quality/query_dashboard/"
#         "specific_form_queries_dashboard.html"
#     )

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         request = self.request

#         # ── Role context ─────────────────────────────────────────────
#         role_context = get_role_context(request.user)
#         is_admin = role_context.get("is_admin", False)
#         is_reviewer = role_context.get("is_reviewer", False)
#         is_zonal_lab = role_context.get("is_zonal_lab", False)
#         is_superuser = request.user.is_superuser

#         is_privileged = is_admin or is_reviewer or is_superuser

#         # ── Zone / Site mappings ─────────────────────────────────────
#         zones = {z.id: z.name for z in role_context.get("zones", [])}
#         sites = {s.id: s.name for s in role_context.get("sites", [])}

#         # ── GET params ───────────────────────────────────────────────
#         zone_id = request.GET.get("zone")
#         site_id = request.GET.get("site")

#         zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
#         site_id_int = int(site_id) if site_id and site_id.isdigit() else None

#         selected_zone_name = zones.get(zone_id_int, "All Zones") if zone_id_int else "All Zones"
#         selected_site_name = sites.get(site_id_int, "All Sites") if site_id_int else "All Sites"

#         # ── Get all DQ counts and problem lists using new service ──
#         role_key = "privileged" if is_privileged else "zonal_lab" if is_zonal_lab else "default"
#         dq_data = get_specific_form_dq_counts(request.user, zone_id_int, site_id_int, role=role_key)

#         # ── Context ──────────────────────────────────────────────────
#         context.update({
#             "is_admin": is_admin,
#             "is_reviewer": is_reviewer,
#             "is_zonal_lab": is_zonal_lab,
#             "is_privileged": is_privileged,

#             "zones": zones,
#             "sites": sites,

#             "selected_zone": zone_id or "",
#             "selected_site": site_id or "",
#             "selected_zone_name": selected_zone_name,
#             "selected_site_name": selected_site_name,

#             "screening_report_total": dq_data["screening_report_total"],
#             "enrollment_report_total": dq_data["enrollment_report_total"],
#             "regimen_report_total": dq_data["regimen_report_total"],
#             "diagnosis_report_total": dq_data["diagnosis_report_total"],
#             "clinic_report_total": dq_data["clinic_report_total"],
#             "zonal_report_total": dq_data["zonal_report_total"],

#             "specific_queries_total": dq_data["total_issues"],
#             "problem_lists": dq_data["problem_lists"],
#         })

#         return context


from django.views.generic import TemplateView
from utils.roles import get_role_context

from reports.services.screening_dq_counts import get_screening_dq_counts
from reports.services.enrollment_dq_counts import get_enrollment_dq_counts
from reports.services.regimen_dq_counts import get_regimen_dq_counts
from reports.services.diagnosis_dq_counts import get_diagnosis_dq_counts
from reports.services.clinic_dq_counts import get_clinic_dq_counts
from reports.services.zonal_dq_counts import get_zonal_dq_counts
from nanopore.models import ZonalLaboratory  # replace with the correct model for screening counts
from utils.permissions import filter_queryset_by_user_role

class SpecificFormQueriesDashboardView(TemplateView):
    template_name = (
        "reports/data_quality/query_dashboard/"
        "specific_form_queries_dashboard.html"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        # ── Role context ─────────────────────────────────────────────
        role_context = get_role_context(request.user)
        is_admin     = role_context.get("is_admin", False)
        is_reviewer  = role_context.get("is_reviewer", False)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_superuser = request.user.is_superuser

        is_privileged = is_admin or is_reviewer or is_superuser

        # ── Zone / Site mappings ─────────────────────────────────────
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # ── GET params ───────────────────────────────────────────────
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else "All Zones"
        selected_site_name = sites.get(site_id_int, "") if site_id_int else "All Sites"

        # ── Data Quality Totals (SERVICE LAYER) ──────────────────────
        screening_total = get_screening_dq_counts(
            request.user, zone_id_int, site_id_int
        ).get("total_issues", 0)

        enrollment_total = get_enrollment_dq_counts(
            request.user, zone_id_int, site_id_int
        ).get("total_issues", 0)

        regimen_total = get_regimen_dq_counts(
            request.user, zone_id_int, site_id_int
        ).get("total_issues", 0)

        diagnosis_total = get_diagnosis_dq_counts(
            request.user, zone_id_int, site_id_int
        ).get("total_issues", 0)

        clinic_total = get_clinic_dq_counts(
            request.user, zone_id_int, site_id_int
        ).get("total_issues", 0)

        # zonal_total = get_zonal_dq_counts(
        #     request.user, zone_id_int, site_id_int
        # ).get("total_issues", 0)
        
        # --- ZONAL COUNTS (fixed) ---
        qs = ZonalLaboratory.objects.select_related(
            "screening","screening__site","screening__site__district__region__zone"
        ).order_by(
            "screening__site__district__region__name","screening__site__name","screening__pid"
        )

        # Filter by user role (user first, then queryset)
        qs = filter_queryset_by_user_role(request.user, qs, site_field="screening__site")

        # Apply zone / site filters
        if zone_id:
            qs = qs.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(screening__site_id=site_id)

        zonal_counts = get_zonal_dq_counts(qs)
        zonal_total = zonal_counts.get("total_issues", 0)

        # ── Combined Total (simple sum) ──────────────────────────────
        specific_queries_total = (
            screening_total +
            enrollment_total +
            regimen_total +
            diagnosis_total +
            clinic_total +
            zonal_total
        )
        
        # ── Combined Total (role-aware) ──────────────────────────────
        # if is_privileged:
        #     specific_queries_total = (
        #         screening_total +
        #         enrollment_total +
        #         regimen_total +
        #         diagnosis_total +
        #         clinic_total +
        #         zonal_total
        #     )
        # elif is_zonal_lab:
        #     specific_queries_total = zonal_total
        # else:
        #     specific_queries_total = (
        #         screening_total +
        #         enrollment_total +
        #         regimen_total +
        #         diagnosis_total +
        #         clinic_total
        #     )

        # ── Context ──────────────────────────────────────────────────
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

            "screening_report_total": screening_total,
            "enrollment_report_total": enrollment_total,
            "regimen_report_total": regimen_total,
            "diagnosis_report_total": diagnosis_total,
            "clinic_report_total": clinic_total,
            "zonal_report_total": zonal_total,

            "specific_queries_total": specific_queries_total,
        })

        return context
