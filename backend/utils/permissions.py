# utils/permissions.py
from django.db.models import Q
from locations.models import Site


def filter_queryset_by_user_role(user, qs, site_field="site"):
    if not hasattr(user, "is_superuser"):
        raise TypeError(f"Expected a single User object, got {type(user)}")
    """
    Filters a queryset based on user role and site/zone level.

    Roles:
    - ADMIN & REVIEWER: full access
    - NURSE & CLINICIAN: records from ALL their assigned sites
    - LABORATORY_TECHNICIAN:
        * Zonal → all records in the zones of ALL their assigned sites
        * National → all records in the countries of ALL their assigned sites
        * Otherwise → records from ALL their assigned sites directly
    """
    # --- Admin, Reviewer & Data Specialist: unrestricted ---
    is_data_specialist = hasattr(user, "profile") and user.profile.position and user.profile.position.name.lower() == "data specialist"
    if user.is_superuser or user.groups.filter(name__in=["ADMIN", "REVIEWER"]).exists() or is_data_specialist:
        return qs

    # --- Must have a profile + at least one site ---
    if not hasattr(user, "profile") or not user.profile.sites.exists():
        return qs.none()

    user_sites = list(user.profile.sites.all())

    # --- Laboratory Technician ---
    if user.groups.filter(name="LABORATORY_TECHNICIAN").exists():
        combined_q = Q()
        for site in user_sites:
            site_level = site.site_level.code.lower() if site.site_level else ""
            if site_level == "zonal":
                try:
                    user_zone = site.district.region.zone
                    combined_q |= Q(**{f"{site_field}__district__region__zone": user_zone})
                except AttributeError:
                    combined_q |= Q(**{f"{site_field}": site})
            elif site_level == "national":
                try:
                    user_country = site.district.region.zone.country
                    combined_q |= Q(**{f"{site_field}__district__region__zone__country": user_country})
                except AttributeError:
                    combined_q |= Q(**{f"{site_field}": site})
            else:
                combined_q |= Q(**{f"{site_field}": site})
        return qs.filter(combined_q).distinct()

    # --- Nurse & Clinician: records from ALL their assigned sites ---
    if user.groups.filter(name__in=["NURSE", "CLINICIAN"]).exists():
        return qs.filter(**{f"{site_field}__in": user_sites}).distinct()

    # --- Default: deny access ---
    return qs.none()
