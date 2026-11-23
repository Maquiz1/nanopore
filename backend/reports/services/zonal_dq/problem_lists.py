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


def query_records(qs, key, duplicate_lab_numbers):
    """The records one query flags, as counted (None: no such query on this form)."""
    if key == "duplicate_unique_lab_no":
        return qs.filter(unique_lab_no__in=duplicate_lab_numbers)
    q_filter = get_zonal_dq_filters(qs.model).get(key)
    return qs.filter(q_filter) if q_filter else None


def serialize_rows(records, key):
    """Rows for a query's list, each with the link to the form that fixes it."""
    name = fix_url_name(key)
    rows = [serialize_record(z, ZONAL_DQ_FIELD_MAPPING[key]) for z in records]
    for item in rows:
        item["fix_url"] = reverse(name, args=[item["zonal_id"]]) if item["zonal_id"] else ""
    return rows


def query_label(key):
    """'missing_lj_results_date' -> 'Missing LJ results date'."""
    if key in QUERY_LABELS:
        return QUERY_LABELS[key]
    words = key.replace("_", " ").split()
    words = [ABBREVIATIONS.get(word, word) for word in words]
    return " ".join(words)[:1].upper() + " ".join(words)[1:]


QUERY_LABELS = {
    "missing_phenotypic_performed": "Positive culture without DST",
    "duplicate_unique_lab_no": "Duplicate unique lab number",
}
ABBREVIATIONS = {"lj": "LJ", "mgit": "MGIT", "dst": "DST", "lpa": "LPA", "lpa1": "LPA1", "lpa2": "LPA2", "mtb": "MTB",
                 "rif": "RIF", "inh": "INH", "xdr": "XDR", "epi": "EPI", "me": "ME", "no": "no."}


def get_zonal_problem_lists(qs, duplicate_lab_numbers, limit=None):
    """
    Build problem lists for each DQ key: the first `limit` records of each (all when None).
    Uses unified Zonal DQ filters for exact parity with counts.
    """
    problem_lists = {}
    for key in ZONAL_DQ_FIELD_MAPPING:
        records = query_records(qs, key, duplicate_lab_numbers)
        if records is None:
            problem_lists[key] = []
            continue
        problem_lists[key] = serialize_rows(records[:limit] if limit else records, key)
    return problem_lists

