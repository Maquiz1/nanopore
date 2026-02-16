# queryset builders

from utils.permissions import filter_queryset_by_user_role

def get_zonal_queryset(user, ZonalModel, zone_id=None, site_id=None):
    qs = ZonalModel.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district__region__zone",
    )

    qs = filter_queryset_by_user_role(user, qs, site_field="screening__site")

    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)

    if site_id:
        qs = qs.filter(screening__site_id=site_id)

    return qs
