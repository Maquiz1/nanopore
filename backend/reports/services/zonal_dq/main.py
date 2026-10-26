# main entrypoint to call everything

from .queryset import get_zonal_queryset
from .stats import get_zonal_stats
from .problem_lists import get_zonal_problem_lists

def get_zonal_counts(user, ZonalModel, zone_id=None, site_id=None):
    """Counts only (stats, total): for sidebar totals and snapshots, which don't need the problem lists."""
    stats, total, _ = get_zonal_stats(get_zonal_queryset(user, ZonalModel, zone_id, site_id).order_by())
    return stats, total


def get_zonal_dq(user, ZonalModel, zone_id=None, site_id=None):
    qs = get_zonal_queryset(user, ZonalModel, zone_id, site_id)
    stats, total, duplicates = get_zonal_stats(qs)
    problems = get_zonal_problem_lists(qs, duplicates)
    return qs, stats, total, problems
