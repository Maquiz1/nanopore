# reports/services/overview_dq_counts.py

from reports.services.specific_form_dq import get_specific_form_dq
from reports.services.missing_form_dq import get_missing_forms_dq


def get_total_data_quality_overview(user, zone_id=None, site_id=None, role=None):
    """
    Centralized overview service.
    Combines:
        - Specific form DQ issues
        - Missing form DQ issues
    Returns unified dashboard totals.
    """

    # ── Specific Form DQ ───────────────────────────────────────────
    specific_dq = get_specific_form_dq(
        user=user,
        zone_id=zone_id,
        site_id=site_id,
        role=role,
    )

    # ── Missing Form DQ ────────────────────────────────────────────
    missing_dq = get_missing_forms_dq(
        user=user,
        zone_id=zone_id,
        site_id=site_id,
        role=role,
    )

    # ── Combined Totals ─────────────────────────────────────────────
    total_specific_issues = specific_dq.get("total_issues", 0)
    total_missing_issues = missing_dq.get("total_form_missing", 0)

    grand_total_queries = total_specific_issues + total_missing_issues

    # ── Return Unified Overview ────────────────────────────────────
    return {

        # ── Specific Form Totals ──
        "screening_report_total": specific_dq.get("screening_report_total", 0),
        "enrollment_report_total": specific_dq.get("enrollment_report_total", 0),
        "regimen_report_total": specific_dq.get("regimen_report_total", 0),
        "diagnosis_report_total": specific_dq.get("diagnosis_report_total", 0),
        "clinic_report_total": specific_dq.get("clinic_report_total", 0),
        "zonal_report_total": specific_dq.get("zonal_report_total", 0),

        # ── Missing Form Totals ──
        "missing_enrollment_count": missing_dq.get("missing_enrollment_count", 0),
        "missing_clinic_count": missing_dq.get("missing_clinic_count", 0),
        "missing_diagnosis_count": missing_dq.get("missing_diagnosis_count", 0),
        "missing_regimen_count": missing_dq.get("missing_regimen_count", 0),
        "missing_zonal_count": missing_dq.get("missing_zonal_count", 0),

        # ── Aggregated Totals ──
        "total_specific_issues": total_specific_issues,
        "total_missing_issues": total_missing_issues,
        "grand_total_queries": grand_total_queries,
    }
