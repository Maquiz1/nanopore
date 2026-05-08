# reports/services/zonal_dq/problem_lists.py

from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING
from .serializers import serialize_record
from .filters import get_zonal_dq_filters

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

    return problem_lists

