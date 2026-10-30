# record serialization

def isolate_number(z):
    """What the Isolate Lab No. column shows; it depends on question 11, submitted to CTRL."""
    if z.culture_isolate_id is None:
        return "Not answered"
    if z.culture_isolate_id != 1:  # No / NA: no isolate went to CTRL
        return "N/A"
    return z.isolate_unique_lab_no or "Not entered"


def serialize_record(z, fields):
    screening = getattr(z, "screening", None)
    site = getattr(screening, "site", None) if screening else None
    zone_name = getattr(getattr(getattr(site, "district", None), "region", None), "zone", None)
    zone_name = getattr(zone_name, "name", "") if zone_name else ""

    data = {
        "id": z.id,
        "zonal_id": getattr(getattr(screening, "zonal_laboratory", None), "id", None),  # fixes are made on Zonal Lab
        "pid": getattr(screening, "pid", "") if screening else "",
        "lab_no": z.unique_lab_no,
        "isolate_no": isolate_number(z),
        "zone_name": zone_name,
        "site_name": getattr(site, "name", "") if site else "",
    }

    for f in fields:
        data[f] = getattr(z, f, None)

    return data
