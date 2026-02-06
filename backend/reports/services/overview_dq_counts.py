from reports.services.missing_form_dq_counts import get_missing_forms_counts
from reports.services.screening_dq_counts import get_screening_dq_counts
from reports.services.enrollment_dq_counts import get_enrollment_dq_counts
from reports.services.regimen_dq_counts import get_regimen_dq_counts
from reports.services.diagnosis_dq_counts import get_diagnosis_dq_counts
from reports.services.clinic_dq_counts import get_clinic_dq_counts
from reports.services.zonal_dq_counts import get_zonal_dq_counts
from nanopore.models import ZonalLaboratory  # replace with the correct model for screening counts
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

def get_data_quality_overview(user, zone_id=None, site_id=None):
    """
    Aggregates ALL data quality metrics for overview dashboard
    """

    # Missing forms
    forms_counts = get_missing_forms_counts(
        user=user,
        zone_id=zone_id,
        site_id=site_id,
    )

    # Field-level queries
    screening_counts = get_screening_dq_counts(
        user=user,
        zone_id=zone_id,
        site_id=site_id,
    )
    
    enrollment_counts = get_enrollment_dq_counts(
        user=user,
        zone_id=zone_id,
        site_id=site_id,
    )
        
    regimen_counts = get_regimen_dq_counts(
        user=user,
        zone_id=zone_id,
        site_id=site_id,
    )
            
    diagnosis_counts = get_diagnosis_dq_counts(
        user=user,
        zone_id=zone_id,
        site_id=site_id,
    )
                
    clinic_counts = get_clinic_dq_counts(
        user=user,
        zone_id=zone_id,
        site_id=site_id,
    )
                    
    # zonal_counts = get_zonal_dq_counts(
    #     user=user,
    #     zone_id=zone_id,
    #     site_id=site_id,
    # )
    
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

    zonal_counts = get_zonal_dq_counts(qs)



    total_issues = (
        screening_counts.get("total_issues", 0) +
        enrollment_counts.get("total_issues", 0) +
        regimen_counts.get("total_issues", 0) +
        diagnosis_counts.get("total_issues", 0) +
        clinic_counts.get("total_issues", 0) +
        zonal_counts.get("total_issues", 0)
    )
    total_form_missing = forms_counts.get("total_form_missing", 0)
    specific_queries_total = total_issues

    return {
        "forms_report_total": forms_counts,
        "specific_queries_total": specific_queries_total,
        "total_issues": total_form_missing + specific_queries_total,
    }
