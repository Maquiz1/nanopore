# # reports/services/specific_form_dq_counts.py

# from reports.services.screening_dq import get_screening_queryset, get_screening_dq
# from reports.services.enrollment_dq import get_enrollment_queryset, get_enrollment_dq
# from reports.services.regimen_dq import get_regimen_queryset, get_regimen_dq
# from reports.services.diagnosis_dq import get_diagnosis_queryset, get_diagnosis_dq
# from reports.services.clinic_dq import get_clinic_queryset, get_clinic_dq
# from reports.services.zonal_dq.main import get_zonal_dq
# from nanopore.models import ZonalLaboratory
# from utils.permissions import filter_queryset_by_user_role


# def get_specific_form_dq_counts(user, zone_id=None, site_id=None, role=None):
#     """
#     Returns a dictionary of all specific form DQ problem lists and totals.
#     Fully service-style using querysets + DQ functions.
#     """

#     # ── Screening ──
#     screening_qs = get_screening_queryset(user, zone_id, site_id)
#     screening_problems, screening_totals = get_screening_dq(screening_qs, user)

#     # ── Enrollment ──
#     enrollment_qs = get_enrollment_queryset(user, zone_id, site_id)
#     enrollment_problems, enrollment_totals = get_enrollment_dq(enrollment_qs)

#     # ── Regimen ──
#     regimen_qs = get_regimen_queryset(user, zone_id, site_id)
#     regimen_problems, regimen_totals = get_regimen_dq(regimen_qs)

#     # ── Diagnosis ──
#     diagnosis_qs = get_diagnosis_queryset(user, zone_id, site_id)
#     diagnosis_problems, diagnosis_totals = get_diagnosis_dq(diagnosis_qs)

#     # ── Clinic ──
#     clinic_qs = get_clinic_queryset(user, zone_id, site_id)
#     clinic_problems, clinic_totals = get_clinic_dq(clinic_qs)

#     # ── Zonal ──
#     zonal_problems, zonal_totals = get_zonal_dq(user, ZonalLaboratory, zone_id, site_id)

#     # ── Role-based total calculation ──
#     if role == "privileged":
#         total = (
#             screening_totals["screening_report_total"]
#             + enrollment_totals["enrollment_report_total"]
#             + regimen_totals["regimen_report_total"]
#             + diagnosis_totals.get("diagnosis_report_total", 0)
#             + clinic_totals.get("clinic_report_total", 0)
#             + zonal_totals.get("total_issues", 0)
#         )
#     elif role == "zonal_lab":
#         total = zonal_totals.get("total_issues", 0)
#     else:
#         total = (
#             screening_totals["screening_report_total"]
#             + enrollment_totals["enrollment_report_total"]
#             + regimen_totals["regimen_report_total"]
#             + diagnosis_totals.get("diagnosis_report_total", 0)
#             + clinic_totals.get("clinic_report_total", 0)
#         )

#     # ── Return structured dict ──
#     return {
#         "screening_report_total": screening_totals["screening_report_total"],
#         "enrollment_report_total": enrollment_totals["enrollment_report_total"],
#         "regimen_report_total": regimen_totals["regimen_report_total"],
#         "diagnosis_report_total": diagnosis_totals.get("diagnosis_report_total", 0),
#         "clinic_report_total": clinic_totals.get("clinic_report_total", 0),
#         "zonal_report_total": zonal_totals.get("total_issues", 0),
#         "problem_lists": {
#             "screening": screening_problems,
#             "enrollment": enrollment_problems,
#             "regimen": regimen_problems,
#             "diagnosis": diagnosis_problems,
#             "clinic": clinic_problems,
#             "zonal": zonal_problems,
#         },
#         "total_by_role": {
#             "privileged": (
#                 screening_totals["screening_report_total"]
#                 + enrollment_totals["enrollment_report_total"]
#                 + regimen_totals["regimen_report_total"]
#                 + diagnosis_totals.get("diagnosis_report_total", 0)
#                 + clinic_totals.get("clinic_report_total", 0)
#                 + zonal_totals.get("total_issues", 0)
#             ),
#             "zonal_lab": zonal_totals.get("total_issues", 0),
#             "default": (
#                 screening_totals["screening_report_total"]
#                 + enrollment_totals["enrollment_report_total"]
#                 + regimen_totals["regimen_report_total"]
#                 + diagnosis_totals.get("diagnosis_report_total", 0)
#                 + clinic_totals.get("clinic_report_total", 0)
#             ),
#         },
#         "total_issues": total,
#     }






# reports/services/specific_form_dq_counts.py
from reports.services.screening_dq_counts import get_screening_dq_counts
from reports.services.enrollment_dq_counts import get_enrollment_dq_counts
from reports.services.regimen_dq_counts import get_regimen_dq_counts
from reports.services.diagnosis_dq_counts import get_diagnosis_dq_counts
from reports.services.clinic_dq_counts import get_clinic_dq_counts
from reports.services.zonal_dq_counts import get_zonal_dq_counts
from nanopore.models import ZonalLaboratory  # replace with the correct model for screening counts
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

def get_specific_form_dq_counts(user, zone_id=None, site_id=None,role=None):
    """
    Returns a dictionary of all specific form data quality totals
    + combined total according to role
    """
    screening_total = get_screening_dq_counts(user, zone_id, site_id).get("total_issues", 0)
    enrollment_total = get_enrollment_dq_counts(user, zone_id, site_id).get("total_issues", 0)
    regimen_total = get_regimen_dq_counts(user, zone_id, site_id).get("total_issues", 0)
    diagnosis_total = get_diagnosis_dq_counts(user, zone_id, site_id).get("total_issues", 0)
    clinic_total = get_clinic_dq_counts(user, zone_id, site_id).get("total_issues", 0)
    # zonal_total = get_zonal_dq_counts(user, zone_id, site_id).get("total_issues", 0)
    
    # --- ZONAL COUNTS (fixed) ---
    qs = ZonalLaboratory.objects.select_related(
        "screening","screening__site","screening__site__district__region__zone"
    ).order_by(
        "screening__site__district__region__name","screening__site__name","screening__pid"
    )

    # Filter by user role (user first, then queryset)
    qs = filter_queryset_by_user_role(user, qs, site_field="screening__site")

    # Apply zone / site filters
    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(screening__site_id=site_id)

    zonal_total = get_zonal_dq_counts(qs)


    # ── Role-based combined total ──
    if role == "privileged":
        total = screening_total + enrollment_total + regimen_total + diagnosis_total + clinic_total + zonal_total
    elif role == "zonal_lab":
        total = zonal_total
    else:
        total = screening_total + enrollment_total + regimen_total + diagnosis_total + clinic_total

    return {
        "screening_report_total": screening_total,
        "enrollment_report_total": enrollment_total,
        "regimen_report_total": regimen_total,
        "diagnosis_report_total": diagnosis_total,
        "clinic_report_total": clinic_total,
        "zonal_report_total": zonal_total,
        "total_by_role": {
            "privileged": screening_total + enrollment_total + regimen_total + diagnosis_total + clinic_total + zonal_total,
            "zonal_lab": zonal_total,
            "default": screening_total + enrollment_total + regimen_total + diagnosis_total + clinic_total,
        },
        "total_issues": total,
    }
