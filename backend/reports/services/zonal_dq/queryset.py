# queryset builders

from nanopore.models import EdcsTblisZonal
from nanopore.zonal_rules import LAB_NUMBER_ONLY_Q
from utils.permissions import filter_queryset_by_user_role

def get_zonal_queryset(user, ZonalModel, zone_id=None, site_id=None):
    qs = ZonalModel.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district__region__zone",
        "screening__zonal_laboratory",
    )

    qs = filter_queryset_by_user_role(user, qs, site_field="screening__site")

    # Other zones' EDCS/TBLIS records are daily copies of their Zonal Lab forms:
    # their queries are counted, and fixed, on Zonal Lab.
    if ZonalModel is EdcsTblisZonal:
        qs = qs.filter(LAB_NUMBER_ONLY_Q)

    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)

    if site_id:
        qs = qs.filter(screening__site_id=site_id)

    # Sort by Zone → Site → PID
    qs = qs.order_by(
        "screening__site__district__region__zone__name",
        "screening__site__name",
        "screening__pid"
    )
    
    return qs
