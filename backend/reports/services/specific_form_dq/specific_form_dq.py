from reports.services.screening_dq import get_screening_queryset, get_screening_dq
from reports.services.enrollment_dq import get_enrollment_queryset, get_enrollment_dq
from reports.services.regimen_dq import get_regimen_queryset, get_regimen_dq
from reports.services.diagnosis_dq import get_diagnosis_queryset, get_diagnosis_dq
from reports.services.clinic_dq import get_clinic_queryset, get_clinic_dq
from reports.services.zonal_dq.main import get_zonal_dq
from nanopore.models import ZonalLaboratory

def get_specific_form_dq(user, zone_id=None, site_id=None, role=None):
    """
    Returns all specific form DQ totals and problem lists.
    Fully centralized: screening DQ counts handle role-based logic for not_eligible/duplicates.
    """

    # ── Screening ──
    screening_qs = get_screening_queryset(user, zone_id, site_id)
    screening_problems, screening_totals = get_screening_dq(screening_qs, user)

    # ── Enrollment ──
    enrollment_qs = get_enrollment_queryset(user, zone_id, site_id)
    enrollment_problems, enrollment_totals = get_enrollment_dq(enrollment_qs)

    # ── Regimen ──
    regimen_qs = get_regimen_queryset(user, zone_id, site_id)
    regimen_problems, regimen_totals = get_regimen_dq(regimen_qs)

    # ── Diagnosis ──
    diagnosis_qs = get_diagnosis_queryset(user, zone_id, site_id)
    diagnosis_problems, diagnosis_totals = get_diagnosis_dq(diagnosis_qs)

    # ── Clinic ──
    clinic_qs = get_clinic_queryset(user, zone_id, site_id)
    clinic_problems, clinic_totals = get_clinic_dq(clinic_qs)

    # ── Zonal ──
    qs, zonal_stats, zonal_total, zonal_problems = get_zonal_dq(user, ZonalLaboratory, zone_id, site_id)

    # ── Role-based total calculation ──
    if role == "privileged":
        total_issues = (
            screening_totals["screening_report_total"]
            + enrollment_totals["enrollment_report_total"]
            + regimen_totals["regimen_report_total"]
            + diagnosis_totals.get("diagnosis_report_total", 0)
            + clinic_totals.get("clinic_report_total", 0)
            + zonal_total
        )
    elif role == "zonal_lab":
        total_issues = zonal_total
    else:  # default for normal users
        total_issues = (
            screening_totals["screening_report_total"]
            + enrollment_totals["enrollment_report_total"]
            + regimen_totals["regimen_report_total"]
            + diagnosis_totals.get("diagnosis_report_total", 0)
            + clinic_totals.get("clinic_report_total", 0)
        )

    return {
        "problem_lists": {
            "screening": screening_problems,
            "enrollment": enrollment_problems,
            "regimen": regimen_problems,
            "diagnosis": diagnosis_problems,
            "clinic": clinic_problems,
            "zonal": zonal_problems,
        },
        "screening_report_total": screening_totals["screening_report_total"],
        "enrollment_report_total": enrollment_totals["enrollment_report_total"],
        "regimen_report_total": regimen_totals["regimen_report_total"],
        "diagnosis_report_total": diagnosis_totals.get("diagnosis_report_total", 0),
        "clinic_report_total": clinic_totals.get("clinic_report_total", 0),
        "zonal_report_total": zonal_total,
        "total_issues": total_issues,
    }
