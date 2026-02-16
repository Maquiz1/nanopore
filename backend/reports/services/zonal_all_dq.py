# reports/services/zonal_dq.py
from django.db.models import Q, Count
from utils.permissions import filter_queryset_by_user_role
from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING

# ─────────────────────────────────────────────
# BASE QUERYSET
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# DUPLICATES
# ─────────────────────────────────────────────

def get_duplicate_lab_numbers(qs):
    return (
        qs.exclude(unique_lab_no__isnull=True)
          .exclude(unique_lab_no="")
          .values("unique_lab_no")
          .annotate(cnt=Count("id"))
          .filter(cnt__gt=1)
          .values_list("unique_lab_no", flat=True)
    )


# ─────────────────────────────────────────────
# AGGREGATES
# ─────────────────────────────────────────────

def get_zonal_stats(qs):
    duplicates = get_duplicate_lab_numbers(qs)

    stats = qs.aggregate(
        missing_unique_lab_no=Count("id", filter=Q(unique_lab_no__isnull=True) | Q(unique_lab_no="")),
        duplicate_unique_lab_no=Count("id", filter=Q(unique_lab_no__in=duplicates)),
        missing_date_sputum_received=Count("id", filter=Q(date_sputum_received__isnull=True)),
        missing_sample_volume=Count("id", filter=Q(sample_volume__isnull=True)),
        missing_appearance=Count("id", filter=Q(appearance__isnull=True)),
    )

    total = sum(stats.values())

    return stats, total, duplicates


# ─────────────────────────────────────────────
# SERIALIZER
# ─────────────────────────────────────────────

def serialize_record(z, fields):
    screening = z.screening
    site = screening.site if screening else None
    zone = getattr(getattr(site.district.region, "zone", None), "name", "")

    data = {
        "id": z.id,
        "pid": getattr(screening, "pid", ""),
        "zone_name": zone,
        "site_name": getattr(site, "name", ""),
    }

    for f in fields:
        data[f] = getattr(z, f, None)

    return data


# ─────────────────────────────────────────────
# PROBLEM LISTS
# ─────────────────────────────────────────────

def get_zonal_problem_lists(qs, duplicates):
    results = {}

    for key, fields in ZONAL_DQ_FIELD_MAPPING.items():

        if key == "duplicate_unique_lab_no":
            results[key] = [
                serialize_record(z, fields)
                for z in qs.filter(unique_lab_no__in=duplicates)[:100]
            ]
            continue

        q = Q()
        model = qs.model

        for f in fields:
            field = model._meta.get_field(f)

            if field.get_internal_type() in ("CharField", "TextField"):
                q |= Q(**{f + "__isnull": True}) | Q(**{f + "": ""})
            else:
                q |= Q(**{f + "__isnull": True})

        results[key] = [
            serialize_record(z, fields)
            for z in qs.filter(q)[:100]
        ]

    return results


# ─────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────

def get_zonal_dq(user, ZonalModel, zone_id=None, site_id=None):

    qs = get_zonal_queryset(user, ZonalModel, zone_id, site_id)

    stats, total, duplicates = get_zonal_stats(qs)

    problems = get_zonal_problem_lists(qs, duplicates)

    return qs, stats, total, problems
