def resolve_substudy_target(role_ctx, field_name, default):
    """
    Resolve target based on role hierarchy:
    Site → Zone → Country
    """

    site = role_ctx.get("site")
    zone = role_ctx.get("zone")
    country = role_ctx.get("country")

    if site and getattr(site, field_name, None):
        return getattr(site, field_name)

    if zone and getattr(zone, field_name, None):
        return getattr(zone, field_name)

    if country and getattr(country, field_name, None):
        return getattr(country, field_name)

    return default
