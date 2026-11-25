"""
Accepted checks: an item on a check list confirmed as correct as it is (nanopore.models.AcceptedCheck).

  list_key          the list (LISTS below); check_key: the check on it (a date check, a substudy query...)
  object_id         the record on the list (its pk; a TB-LIS lab number on TB-LIS follow-up)
  values            what the check looked at, when it was accepted. If those values change
                    later the acceptance no longer holds and the item is back on the list,
                    so an acceptance never hides a new problem.

Accepted items leave the list's counts (the sidebar badges, Your work today, the snapshots)
and are shown on the list's Accepted tab, with Undo. Data specialists, data managers and
admins accept (utils.access.ACCEPT_CHECKS). An accepted lab check also tells TB-LIS uploads
and the nightly sync to leave the Zonal Lab record as it is (nanopore/study_lock.py).
"""
import datetime
import decimal
import hashlib
import json

from django.utils import timezone

DATE_ISSUES, DSDR, UNTREATED, NO_DST, TBLIS_FOLLOW_UP, SUBSTUDY = (
    "date_issues", "dsdr", "untreated", "no_dst", "tblis_follow_up", "substudy")
LISTS = {
    DATE_ISSUES: "Date issues",
    DSDR: "DS / DR checks",
    UNTREATED: "Outcome without treatment",
    NO_DST: "Positive culture, no DST",
    TBLIS_FOLLOW_UP: "TB-LIS follow-up",
    SUBSTUDY: "Substudy queries",
}


def plain(value):
    """A value as JSON keeps it: options by their pk, dates as text."""
    if hasattr(value, "pk"):
        return value.pk
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return sorted((plain(v) for v in value), key=str)
    if isinstance(value, str):
        return value.strip() or None
    return value


def fingerprint(values):
    data = json.dumps({k: plain(v) for k, v in values.items()}, sort_keys=True, default=str)
    return hashlib.sha256(data.encode()).hexdigest()


def _active(list_key):
    """{check_key: {object_id: AcceptedCheck}} of the list's acceptances (read once per request)."""
    from nanopore.models import AcceptedCheck
    from nanopore.study_lock import _memo
    memo = _memo.get()
    key = f"accepted:{list_key}"
    if memo is not None and key in memo:
        return memo[key]
    found = {}
    for accepted in AcceptedCheck.objects.filter(list_key=list_key, revoked_at__isnull=True).select_related("accepted_by"):
        found.setdefault(accepted.check_key, {})[accepted.object_id] = accepted
    if memo is not None:
        memo[key] = found
    return found


def _forget(list_key):
    from nanopore.study_lock import _memo
    memo = _memo.get()
    if memo is not None:
        memo.pop(f"accepted:{list_key}", None)


def holding(list_key, check_key, objects, values_of, key=lambda obj: obj.pk):
    """{object_id: AcceptedCheck} of the objects whose acceptance still holds (values unchanged)."""
    accepted = _active(list_key).get(check_key, {})
    if not accepted:
        return {}
    found = {}
    for obj in objects:
        one = accepted.get(str(key(obj)))
        if one is not None and one.fingerprint == fingerprint(values_of(obj)):
            found[str(key(obj))] = one
    return found


def split(qs, list_key, check_key, values_of):
    """(still to check, accepted) of a queryset of records on a list."""
    accepted = _active(list_key).get(check_key, {})
    if not accepted:
        return qs, qs.none()
    candidates = qs.filter(pk__in=[int(i) for i in accepted if str(i).isdigit()])
    kept = holding(list_key, check_key, candidates, values_of)
    ids = [int(i) for i in kept]
    return qs.exclude(pk__in=ids), qs.filter(pk__in=ids)


def lapsed(list_key, check_key, objects, values_of, key=lambda obj: obj.pk):
    """object ids accepted earlier whose values have changed since (shown as "Data changed since accepted")."""
    accepted = _active(list_key).get(check_key, {})
    return {str(key(obj)) for obj in objects
            if str(key(obj)) in accepted and accepted[str(key(obj))].fingerprint != fingerprint(values_of(obj))}


def accept(user, list_key, check_key, object_id, values, reason, screening=None, zonal_lab=None):
    from nanopore.models import AcceptedCheck
    AcceptedCheck.objects.filter(list_key=list_key, check_key=check_key, object_id=str(object_id),
                                 revoked_at__isnull=True).update(revoked_at=timezone.now(), revoked_by=user)
    _forget(list_key)
    return AcceptedCheck.objects.create(
        list_key=list_key, check_key=check_key, object_id=str(object_id), screening=screening, zonal_lab=zonal_lab,
        values={k: plain(v) for k, v in values.items()}, fingerprint=fingerprint(values), reason=reason, accepted_by=user)


def undo(user, list_key, check_key, object_id):
    from nanopore.models import AcceptedCheck
    _forget(list_key)
    return AcceptedCheck.objects.filter(list_key=list_key, check_key=check_key, object_id=str(object_id),
                                        revoked_at__isnull=True).update(revoked_at=timezone.now(), revoked_by=user)


def accepted_count(list_key):
    from nanopore.models import AcceptedCheck
    return AcceptedCheck.objects.filter(list_key=list_key, revoked_at__isnull=True).count()
