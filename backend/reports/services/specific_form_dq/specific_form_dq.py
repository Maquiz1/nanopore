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

    # Default payloads to zeros to prevent leakage and handle dynamic roles cleanly
    s_probs, e_probs, r_probs, d_probs, c_probs, z_probs = {}, {}, {}, {}, {}, {}
    s_tot, e_tot, r_tot, d_tot, c_tot, z_tot = 0, 0, 0, 0, 0, 0

    # ── Execute Queries based strictly on Role Access ──
    # Privileged & Normal users get the standard forms
    if role in ["privileged", "default"]:
        screening_qs = get_screening_queryset(user, zone_id, site_id)
        s_probs, s_totals = get_screening_dq(screening_qs, user)
        s_tot = s_totals.get("screening_report_total", 0)

        enrollment_qs = get_enrollment_queryset(user, zone_id, site_id)
        e_probs, e_totals = get_enrollment_dq(enrollment_qs)
        e_tot = e_totals.get("enrollment_report_total", 0)

        regimen_qs = get_regimen_queryset(user, zone_id, site_id)
        r_probs, r_totals = get_regimen_dq(regimen_qs)
        r_tot = r_totals.get("regimen_report_total", 0)

        diagnosis_qs = get_diagnosis_queryset(user, zone_id, site_id)
        d_probs, d_totals = get_diagnosis_dq(diagnosis_qs)
        d_tot = d_totals.get("diagnosis_report_total", 0)

        clinic_qs = get_clinic_queryset(user, zone_id, site_id)
        c_probs, c_totals = get_clinic_dq(clinic_qs)
        c_tot = c_totals.get("clinic_report_total", 0)

    # Privileged & Zonal Lab users get the Zonal forms
    if role in ["privileged", "zonal_lab"]:
        qs, zonal_stats, z_tot, z_probs = get_zonal_dq(user, ZonalLaboratory, zone_id, site_id)

    # ── Sum the requested issues ──
    total_issues = s_tot + e_tot + r_tot + d_tot + c_tot + z_tot

    return {
        "problem_lists": {
            "screening": s_probs,
            "enrollment": e_probs,
            "regimen": r_probs,
            "diagnosis": d_probs,
            "clinic": c_probs,
            "zonal": z_probs,
        },
        "screening_report_total": s_tot,
        "enrollment_report_total": e_tot,
        "regimen_report_total": r_tot,
        "diagnosis_report_total": d_tot,
        "clinic_report_total": c_tot,
        "zonal_report_total": z_tot,
        "total_issues": total_issues,
    }
