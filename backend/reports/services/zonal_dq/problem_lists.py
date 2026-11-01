# reports/services/zonal_dq/problem_lists.py

from django.urls import reverse

from nanopore.zonal_rules import NANOPORE_PREFIXES
from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING
from .serializers import serialize_record
from .filters import get_zonal_dq_filters

def fix_url_name(key):
    """The form that answers a Dar es Salaam query (EDCS/TBLIS records are read only)."""
    if key in ("missing_first_line_drugs", "missing_second_line_drugs"):
        return "nanopore:ctrl-dar-lpa"
    if ZONAL_DQ_FIELD_MAPPING[key][0].startswith(NANOPORE_PREFIXES):
        return "nanopore:ctrl-dar-nanopore"
    return "nanopore:zonal-laboratory-update"  # lab number: fix it there and upload TB-LIS again


def get_zonal_problem_lists(qs, duplicate_lab_numbers):
    """
    Build problem lists for each DQ key.
    Uses unified Zonal DQ filters for exact parity with counts.
    """
    problem_lists = {}
    dq_filters = get_zonal_dq_filters(qs.model)

    for key, fields in ZONAL_DQ_FIELD_MAPPING.items():

        # ───────────────── Duplicate labs ─────────────────
        if key == "duplicate_unique_lab_no":
            problem_lists[key] = [
                serialize_record(z, fields)
                for z in qs.filter(unique_lab_no__in=duplicate_lab_numbers)[:10]
            ]
            continue

        q_filter = dq_filters.get(key)
        
        if q_filter:
            problem_lists[key] = [
                serialize_record(z, fields)
                for z in qs.filter(q_filter)[:10]
            ]
        else:
            problem_lists[key] = []

    for key, items in problem_lists.items():
        name = fix_url_name(key)
        for item in items:
            item["fix_url"] = reverse(name, args=[item["zonal_id"]]) if item["zonal_id"] else ""

    return problem_lists

