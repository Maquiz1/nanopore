from reports.context_processors.cache_helpers import cached_context
from reports.services.substudy_queries import substudy_query_counts


@cached_context(ttl=300)
def substudy_queries(request):
    """Sidebar link Substudy queries: shown to users who see any of them, with the number to fix."""
    if not request.user.is_authenticated:
        return {"context_substudy_queries_visible": False, "context_substudy_queries_total": 0}
    counts = substudy_query_counts(request.user)
    return {
        "context_substudy_queries_visible": bool(counts),
        "context_substudy_queries_total": sum(counts.values()),
    }
