# utils/roles.py
from utils.access import (
    ENROLLMENT, LABORATORY_TECHNICIAN, can_view, get_accessible_sites, get_accessible_zones, is_unscoped, has_role,
)
from locations.models import Site


def get_role_context(user):
    """
    Returns role-based context for templates:
    - Role flags (is_admin, is_zonal_lab, etc.)
    - Accessible zones and sites (for filter dropdowns)
    """
    if is_unscoped(user):
        return {
            "is_admin": True,
            "is_zonal_lab": False,
            "is_national_lab": False,
            "is_site_only": False,
            "zones": get_accessible_zones(user),
            "sites": Site.objects.all(),
        }

    sites = get_accessible_sites(user)
    zones = get_accessible_zones(user)
    # "Lab user": a laboratory technician without clinical rights, whatever their
    # assignment (zones, zonal/national lab site or local site). Data-quality
    # pages use this to show lab queries only.
    is_zonal_lab = has_role(user, LABORATORY_TECHNICIAN) and not can_view(user, ENROLLMENT)
    # Lab users covering more than one zone get zone + site filters.
    is_national_lab = is_zonal_lab and zones.count() > 1
    return {
        "is_admin": False,
        "is_zonal_lab": is_zonal_lab,
        "is_national_lab": is_national_lab,
        "is_site_only": not (is_zonal_lab or is_national_lab),
        "zones": zones,
        "sites": sites,
    }
