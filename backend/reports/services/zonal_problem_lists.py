# reports/services/zonal_problem_lists.py
from django.db.models import Q
from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING

def serialize_record(z, fields):
    screening = getattr(z, "screening", None)
    site = getattr(screening, "site", None) if screening else None
    zone_obj = getattr(getattr(getattr(site, "district", None), "region", None), "zone", None)
    record = {
        "id": z.id,
        "pid": getattr(screening, "pid", "") if screening else "",
        "screening_date": getattr(screening, "screening_date", None) if screening else None,
        "zone_name": zone_obj.name if zone_obj else "",
        "site_name": getattr(site, "name", "") if site else "",
    }
    for f in fields:
        record[f] = getattr(z, f, None)
    return record

def get_zonal_problem_lists(qs, duplicate_lab_numbers, all_fields_mapping=ZONAL_DQ_FIELD_MAPPING):
    problem_lists = {}

    for key, fields in all_fields_mapping.items():
        if key == "duplicate_unique_lab_no":
            problem_lists[key] = [
                serialize_record(z, fields)
                for z in qs.filter(unique_lab_no__in=duplicate_lab_numbers)[:100]
            ]
            continue

        q = Q()
        for f in fields:
            q |= Q(**{f + "__isnull": True})

        # Apply conditional guards to match aggregate logic
        if key in ["missing_culture_method","missing_microscopy_type","missing_microscopy_date","missing_microscopy_results"]:
            q &= Q(culture_performed=1)

        if key in ["missing_lj_inoculation_date","missing_lj_results_date","missing_lj_results"]:
            q &= Q(culture_performed=1, culture_method=1)

        if key in ["missing_mgit_inoculation_date","missing_mgit_results_date","missing_mgit_results"]:
            q &= Q(culture_performed=1, culture_method=2)

        if key in ["missing_isolate_date","missing_culture_isolate"]:
            q &= Q(culture_isolate=1)

        if key.startswith("missing_first_line"):
            q &= Q(first_line_lpa=1)

        if key.startswith("missing_second_line"):
            q &= Q(second_line_lpa=1)

        if key.startswith("missing_nanopore"):
            q &= Q(nanopore_done=1)

        if key in ["missing_epi_to_me_date","missing_epi_to_me_version"]:
            q &= Q(epi_to_me=1)

        if key in ["missing_xpert_xdr_date_performed","missing_xpert_xdr_results"]:
            q &= Q(xpert_xdr_performed=1)

        problem_lists[key] = [
            serialize_record(z, fields)
            for z in qs.filter(q)[:100]
        ]

    return problem_lists
