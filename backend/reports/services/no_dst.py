"""
Positive culture, no DST: for the study team to decide whether to ask CTRL for DST in TB-LIS.

Information, never a query (data dictionary D05/D06): not every positive culture gets
DST, and the DST only comes from TB-LIS.

  dar     Dar es Salaam positive cultures (LJ or MGIT) with no phenotypic DST from TB-LIS.
  others  Other zones' isolates CTRL has numbered whose DST isn't in TB-LIS yet.
"""
from reports.services.zonal_dq.ctrl import get_ctrl_dar_queryset, get_ctrl_isolates_queryset, to_complete_q
from reports.services.zonal_dq.filters import waiting_for_dst_filter

GROUPS = (("dar", "Dar es Salaam"), ("others", "Other zones (isolate at CTRL)"))


def no_dst_records(user, group):
    if group == "dar":
        return get_ctrl_dar_queryset(user).filter(waiting_for_dst_filter(dar=True)).order_by(
            "screening__site__name", "screening__pid")
    qs = get_ctrl_isolates_queryset(user)
    # Once CTRL has given the number (before that it is CTRL's query on CTRL isolates)
    return qs.filter(waiting_for_dst_filter(dar=False)).exclude(pk__in=qs.filter(to_complete_q()).values("pk"))


def no_dst_counts(user):
    return {group: no_dst_records(user, group).count() for group, _ in GROUPS}
