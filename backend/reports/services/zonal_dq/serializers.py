# record serialization

def serialize_record(z, fields):
    screening = getattr(z, "screening", None)
    site = getattr(screening, "site", None) if screening else None
    zone_name = getattr(getattr(getattr(site, "district", None), "region", None), "zone", None)
    zone_name = getattr(zone_name, "name", "") if zone_name else ""

    data = {
        "id": z.id,
        "pid": getattr(screening, "pid", "") if screening else "",
        "zone_name": zone_name,
        "site_name": getattr(site, "name", "") if site else "",
    }

    for f in fields:
        data[f] = getattr(z, f, None)

    return data
