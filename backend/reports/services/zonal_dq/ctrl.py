# What CTRL answers for other zones: isolate numbers and phenotypic DST

from django.db.models import Count, Q

from nanopore.zonal_rules import ctrl_records
from .filters import get_ctrl_isolate_filters


def get_ctrl_isolates_queryset(user, zone_id=None, site_id=None):
    qs = ctrl_records(user)
    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(screening__site_id=site_id)
    return qs.order_by("screening__site__district__region__zone__name", "screening__site__name", "screening__pid")


def get_ctrl_isolate_counts(user, zone_id=None, site_id=None):
    """{query: records it flags}, the numbers behind the sidebar, overview and trends."""
    filters = get_ctrl_isolate_filters()
    qs = get_ctrl_isolates_queryset(user, zone_id, site_id).order_by()
    return qs.aggregate(**{key: Count("id", filter=q, distinct=True) for key, q in filters.items()})


def to_complete_q():
    """Records with anything left for CTRL to enter."""
    q = Q(pk__in=[])
    for query in get_ctrl_isolate_filters().values():
        q |= query
    return q
