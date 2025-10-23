def global_total_issues(request):
    """
    Returns the total issues count for the navbar, summing up
    screening, enrollment, and forms reports.
    Assumes the individual counts are calculated elsewhere and
    passed into the template context (e.g., via other context processors or views).
    """
    # Default values if counts are missing
    forms_report_total = getattr(request, 'forms_report_total', 0)
    screening_report_total = getattr(request, 'screening_report_total', 0)
    enrollment_report_total = getattr(request, 'enrollment_report_total', 0)

    total_issues = forms_report_total + screening_report_total + enrollment_report_total

    return {
        "total_issues": total_issues
    }
