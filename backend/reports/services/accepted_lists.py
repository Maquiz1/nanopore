"""
For each check list: find one item the user may see, with the values its acceptance holds on.

find(user, list_key, check_key, object_id) -> Item or None. The Accept button posts the list,
the check and the record; the values are always read again here, never taken from the page.
"""
from dataclasses import dataclass

from reports.services import accepted as acc


@dataclass
class Item:
    obj: object
    values: dict
    screening: object = None
    zonal_lab: object = None


def _zonal_of(screening):
    try:
        return screening.zonal_laboratory
    except Exception:
        return None


def _date_item(user, check_key, object_id, builder=None):
    from reports.services.date_issues import _failing, check_values, is_lab_check, screening_of, visible_checks
    check = next((c for c in visible_checks(user, builder) if c.key == check_key), None)
    if check is None or not str(object_id).isdigit():
        return None
    obj = _failing(user, check).filter(pk=object_id).first()
    if obj is None:
        return None
    screening = screening_of(obj)
    return Item(obj, check_values(check, obj), screening, _zonal_of(screening) if is_lab_check(check) else None)


def _dsdr_item(user, check_key, object_id):
    from reports.services import dsdr_checks
    return _date_item(user, check_key, object_id, dsdr_checks.build_checks)


def untreated_values(screening):
    dx = getattr(screening, "diagnosis", None)
    return {"tb_treatment": getattr(dx, "tb_treatment_id", None), "tb_outcome2": getattr(dx, "tb_outcome2_id", None),
            "tb_outcome2_date": getattr(dx, "tb_outcome2_date", None)}


def _untreated_item(user, check_key, object_id):
    from reports.views.queries.date_issues_view import OutcomeWithoutTreatmentView
    from utils import access
    if not access.can_see_queries(user, access.DIAGNOSIS) or not str(object_id).isdigit():
        return None
    obj = OutcomeWithoutTreatmentView.all_records(user).filter(pk=object_id).first()
    return Item(obj, untreated_values(obj), obj) if obj else None


def _no_dst_item(user, check_key, object_id):
    from reports.services.no_dst import GROUPS, all_no_dst, no_dst_values
    if check_key not in dict(GROUPS) or not str(object_id).isdigit():
        return None
    obj = all_no_dst(user, check_key).filter(pk=object_id).first()
    if obj is None:
        return None
    lab = _zonal_of(obj.screening) if check_key == "dar" else obj
    return Item(obj, no_dst_values(obj), obj.screening, lab)


def _substudy_item(user, check_key, object_id):
    from reports.services.substudy_queries import QUERIES_BY_KEY, all_substudy_query, substudy_values, visible_queries
    query = QUERIES_BY_KEY.get(check_key)
    if query is None or query not in visible_queries(user) or not str(object_id).isdigit():
        return None
    obj = all_substudy_query(user, query).filter(pk=object_id).first()
    return Item(obj, substudy_values(obj), obj, _zonal_of(obj)) if obj else None


def _tblis_item(user, check_key, object_id):
    from nanopore.views.laboratory.edcs_tblis.tblis_follow_up_view import follow_up_item
    return follow_up_item(user, check_key, object_id)


FINDERS = {
    acc.DATE_ISSUES: _date_item,
    acc.DSDR: _dsdr_item,
    acc.UNTREATED: _untreated_item,
    acc.NO_DST: _no_dst_item,
    acc.SUBSTUDY: _substudy_item,
    acc.TBLIS_FOLLOW_UP: _tblis_item,
}


def find(user, list_key, check_key, object_id):
    finder = FINDERS.get(list_key)
    return finder(user, check_key, object_id) if finder else None
