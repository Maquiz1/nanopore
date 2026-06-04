# utils/roles.py
from locations.models import Zone, Site


def get_role_context(user):
    """
    Returns role-based context for templates:
    - Role flags (is_admin, is_zonal_lab, etc.)
    - Accessible zones and sites
    """

    # Default empty context
    context = {
        "is_admin": False,
        "is_zonal_lab": False,
        "is_national_lab": False,
        "is_site_only": False,
        "zones": Zone.objects.none(),
        "sites": Site.objects.none(),
    }

    # Admin, Reviewer, & Data Specialist → full access
    is_data_specialist = hasattr(user, "profile") and user.profile.position and user.profile.position.name.lower() == "data specialist"
    if user.is_superuser or user.groups.filter(name__in=["ADMIN", "REVIEWER"]).exists() or is_data_specialist:
        context.update({
            "is_admin": True,
            "zones": Zone.objects.all(),
            "sites": Site.objects.all(),
        })
        return context

    # Must have profile + at least one site
    if not hasattr(user, "profile") or not user.profile.sites.exists():
        return context

    user_sites = list(user.profile.sites.all())

    # Laboratory Technician — union of zones/sites from all assigned sites
    if user.groups.filter(name="LABORATORY_TECHNICIAN").exists():
        zone_ids = set()
        country_ids = set()
        site_ids = set()
        is_zonal = False
        is_national = False

        for site in user_sites:
            site_level = site.site_level.code.lower() if site.site_level else ""
            try:
                if site_level == "zonal":
                    is_zonal = True
                    zone_ids.add(site.district.region.zone.id)
                elif site_level == "national":
                    is_national = True
                    country_ids.add(site.district.region.zone.country.id)
                else:
                    site_ids.add(site.id)
                    zone_ids.add(site.district.region.zone.id)
            except AttributeError:
                site_ids.add(site.id)

        if is_national:
            accessible_zones = Zone.objects.filter(country__id__in=country_ids)
            accessible_sites = Site.objects.filter(district__region__zone__country__id__in=country_ids)
            context.update({
                "is_national_lab": True,
                "zones": accessible_zones,
                "sites": accessible_sites,
            })
        elif is_zonal:
            accessible_zones = Zone.objects.filter(id__in=zone_ids)
            accessible_sites = Site.objects.filter(district__region__zone__id__in=zone_ids)
            context.update({
                "is_zonal_lab": True,
                "zones": accessible_zones,
                "sites": accessible_sites,
            })
        else:
            accessible_zones = Zone.objects.filter(id__in=zone_ids)
            context.update({
                "is_site_only": True,
                "zones": accessible_zones,
                "sites": Site.objects.filter(id__in=site_ids),
            })
        return context

    # Nurse & Clinician — all their assigned sites
    if user.groups.filter(name__in=["NURSE", "CLINICIAN"]).exists():
        zone_ids = set()
        for site in user_sites:
            try:
                zone_ids.add(site.district.region.zone.id)
            except AttributeError:
                pass
        context.update({
            "is_site_only": True,
            "zones": Zone.objects.filter(id__in=zone_ids),
            "sites": Site.objects.filter(id__in=[s.id for s in user_sites]),
        })
        return context

    return context
