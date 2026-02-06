# utils/permissions.py
from locations.models import Site

def filter_queryset_by_user_role(user, qs, site_field="site"):
    if not hasattr(user, "is_superuser"):
        raise TypeError(f"Expected a single User object, got {type(user)}")
    """
    Filters a queryset based on user role and site/zone level.

    Roles:
    - ADMIN & REVIEWER: full access
    - NURSE & CLINICIAN: always only their own site
    - LABORATORY_TECHNICIAN:
        * Zonal + Laboratory → all records in their zone (all site types)
        * National + Laboratory → all records in their country (all site types)
        * Otherwise → only their own site
    """
    # --- Admin & Reviewer: unrestricted ---
    if user.is_superuser or user.groups.filter(name__in=["ADMIN", "REVIEWER"]).exists():
        return qs

    # --- Must have a profile + site ---
    if not hasattr(user, "profile") or not user.profile.site:
        return qs.none()

    site = user.profile.site
    site_level = site.site_level.code.lower() if site.site_level else ""
    site_type = site.site_type.code.lower() if site.site_type else ""

    # --- Laboratory Technician ---
    if user.groups.filter(name="LABORATORY_TECHNICIAN").exists():
        if site_level == "zonal":
            # All sites in the same zone
            user_zone = site.district.region.zone
            return qs.filter(**{f"{site_field}__district__region__zone": user_zone})
        elif site_level == "national":
            # All sites in the same country
            user_country = site.district.region.zone.country
            return qs.filter(**{f"{site_field}__district__region__zone__country": user_country})
        else:
            # Only their own site
            return qs.filter(**{f"{site_field}": site})

    # --- Nurse & Clinician (always own site only) ---
    if user.groups.filter(name__in=["NURSE", "CLINICIAN"]).exists():
        return qs.filter(**{f"{site_field}": site})

    # --- Default: deny access ---
    return qs.none()
