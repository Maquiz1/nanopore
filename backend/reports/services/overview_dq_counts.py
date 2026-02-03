from reports.services.missing_form_dq_counts import get_missing_forms_counts
from reports.services.screening_dq_counts import get_screening_dq_counts


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

    total_form_missing = forms_counts.get("total_form_missing", 0)
    specific_queries_total = screening_counts.get("total_issues", 0)

    return {
        "forms_report_total": forms_counts,
        "specific_queries_total": specific_queries_total,
        "total_issues": total_form_missing + specific_queries_total,
    }
