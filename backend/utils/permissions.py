# utils/permissions.py
from locations.models import Site

def filter_queryset_by_user_role(user, qs, site_field="site"):
    """
    Filters a queryset based on user role and site/zone level.
    
    Roles:
    - NURSE & CLINICIAN: access to local or zonal clinic sites
    - LABORATORY_TECHNICIAN: access to zonal lab sites (all sites in zone)
    - ADMIN & REVIEWER: access to all data
    """
    if user.groups.filter(name__in=['ADMIN', 'REVIEWER']).exists():
        return qs  # full access

    if not hasattr(user, 'profile') or not user.profile.site:
        return qs.none()  # no site linked → no access

    site = user.profile.site

    # LAB TECH
    if user.groups.filter(name='LABORATORY_TECHNICIAN').exists():
        if site.site_level.code in ['zonal', 'national']:
            # get the zone for the user's site
            user_zone = site.district.region.zone
            return qs.filter(**{f"{site_field}__district__region__zone": user_zone})
        else:
            return qs.none()

    # NURSE & CLINICIAN
    elif user.groups.filter(name__in=['NURSE', 'CLINICIAN']).exists():
        if site.site_level.code == 'local':
            # see only their own site
            return qs.filter(**{f"{site_field}": site})
        elif site.site_level.code == 'zonal':
            # see all clinic sites in their zone
            user_zone = site.district.region.zone
            return qs.filter(**{
                f"{site_field}__district__region__zone": user_zone,
                f"{site_field}__site_type__code": "clinic"
            })
        else:
            return qs.none()

    return qs.none()
