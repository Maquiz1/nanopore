"""The TB-LIS follow-up badge: study participants on the follow-up page's lists, each counted once.

Not part of the query totals: these records already raise EDCS/TBLIS queries; the
badge says how many participants CTRL has to follow up in TB-LIS.
"""
from nanopore import tblis_status
from nanopore.models import ZonalLaboratory
from nanopore.models.discrepancies import TblisFollowUp
from reports.context_processors.cache_helpers import cached_context
from utils import access


def follow_up_participants(user):
    """Screening ids of the participants on TB-LIS follow-up the user may see."""
    labs = ZonalLaboratory.objects.all()
    if not (getattr(user, "is_superuser", False) or access.is_unscoped(user) or access.is_ctrl_lab(user)):
        labs = access.scope_queryset(user, labs, "screening__site")
    from nanopore.views.laboratory.edcs_tblis.tblis_follow_up_view import (
        NOT_RECORDED, RECORD_LISTS, accepted_labs, accepted_rows)
    found = tblis_status.record_statuses(labs)
    ids = set()
    for list_key, state in RECORD_LISTS.items():
        on_list = labs.filter(screening_id__in=[pk for pk, status in found.items() if status.state == state])
        kept = accepted_labs(list_key, on_list, found)  # accepted: followed up, nothing to change
        ids |= set(on_list.exclude(pk__in=[int(pk) for pk in kept]).values_list("screening_id", flat=True))
    rows = list(TblisFollowUp.objects.filter(labno__in=labs.values("unique_lab_no")))
    kept = accepted_rows(rows)
    not_recorded = [row.labno for row in rows if row.labno not in kept]
    ids |= set(labs.filter(unique_lab_no__in=not_recorded).values_list("screening_id", flat=True))
    return ids


@cached_context(ttl=300)
def tblis_follow_up_total(request):
    user = request.user
    if not user.is_authenticated or not access.has_feature(user, access.TBLIS_FOLLOW_UP):
        return {"context_tblis_follow_up_total": 0, "context_no_dst_total": 0, "context_nanopore_failed_total": 0}
    from reports.services.nanopore_failed import nanopore_failed_records
    from reports.services.no_dst import no_dst_counts
    return {"context_tblis_follow_up_total": len(follow_up_participants(user)),
            # Information lists, outside the query totals too
            "context_no_dst_total": sum(no_dst_counts(user).values()),
            "context_nanopore_failed_total": nanopore_failed_records(user).count()}  # open ones: since + before
