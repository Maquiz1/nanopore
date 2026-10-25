from reports.context_processors.cache_helpers import cached_context
from reports.services import dsdr_checks
from reports.services.date_issues import date_issue_counts
from reports.views.queries.date_issues_view import OutcomeWithoutTreatmentView
from utils import access
from utils.access import can_see_queries


@cached_context(ttl=300)
def date_issues(request):
    """Sidebar links Date issues, DS / DR checks and Outcome without treatment, with the number to fix."""
    if not request.user.is_authenticated:
        return {"context_date_issues_visible": False, "context_date_issues_total": 0,
                "context_dsdr_visible": False, "context_dsdr_total": 0,
                "context_outcome_no_treatment_visible": False, "context_outcome_no_treatment_total": 0}
    counts = date_issue_counts(request.user)
    dsdr = date_issue_counts(request.user, builder=dsdr_checks.build_checks)
    outcome_visible = can_see_queries(request.user, access.DIAGNOSIS)
    return {
        "context_date_issues_visible": bool(counts),
        "context_date_issues_total": sum(counts.values()),
        "context_dsdr_visible": bool(dsdr),
        "context_dsdr_total": sum(dsdr.values()),
        "context_outcome_no_treatment_visible": outcome_visible,
        "context_outcome_no_treatment_total": OutcomeWithoutTreatmentView.records(request.user).count() if outcome_visible else 0,
    }
