# What CTRL answers for other zones: isolate numbers and phenotypic DST

from django.db.models import Count, Q

from nanopore.models import EdcsTblisZonal
from nanopore.zonal_rules import LAB_NUMBER_ONLY_Q, NANOPORE_PREFIXES, ctrl_records
from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING
from utils.access import is_ctrl_lab, is_unscoped, scope_queryset
from .filters import _all_filters, get_ctrl_isolate_filters


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


def get_dar_work(user):
    """{tab: (label, EDCS/TBLIS records)}: what CTRL still enters for Dar es Salaam, read from the merged records."""
    qs = EdcsTblisZonal.objects.filter(LAB_NUMBER_ONLY_Q, screening__zonal_laboratory__isnull=False).select_related(
        "screening__site__district__region__zone", "screening__zonal_laboratory")
    if not (is_unscoped(user) or is_ctrl_lab(user)):
        qs = scope_queryset(user, qs, "screening__site")
    filters = _all_filters(EdcsTblisZonal)

    nanopore = Q(pk__in=[])
    for key, fields in ZONAL_DQ_FIELD_MAPPING.items():
        if key in filters and fields[0].startswith(NANOPORE_PREFIXES):
            nanopore |= filters[key]
    lpa = filters["missing_first_line_drugs"] | filters["missing_second_line_drugs"]

    order = ("screening__site__name", "screening__pid")
    return {
        "nanopore": ("Needs Nanopore", qs.filter(nanopore).distinct().order_by(*order)),
        "lpa": ("Needs LPA checkboxes", qs.filter(lpa).distinct().order_by(*order)),
    }
