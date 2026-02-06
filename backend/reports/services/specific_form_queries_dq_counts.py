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
    qs = filter_queryset_by_user_role(user, qs, site_field="site")

    # Apply zone / site filters
    if zone_id:
        qs = qs.filter(site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(site_id=site_id)

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
