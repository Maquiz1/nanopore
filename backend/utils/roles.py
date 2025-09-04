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

    # Admin & Reviewer → full access
    if user.is_superuser or user.groups.filter(name__in=["ADMIN", "REVIEWER"]).exists():
        context.update({
            "is_admin": True,
            "zones": Zone.objects.all(),
            "sites": Site.objects.all(),
        })
        return context

    # Must have profile + site
    if not hasattr(user, "profile") or not user.profile.site:
        return context

    site = user.profile.site
    site_level = site.site_level.code.lower() if site.site_level else ""

    # Laboratory Technician
    if user.groups.filter(name="LABORATORY_TECHNICIAN").exists():
        if site_level == "zonal":
            zone = site.district.region.zone
            context.update({
                "is_zonal_lab": True,
                "zones": Zone.objects.filter(id=zone.id),
                "sites": Site.objects.filter(district__region__zone=zone),
            })
        elif site_level == "national":
            country = site.district.region.zone.country
            context.update({
                "is_national_lab": True,
                "zones": Zone.objects.filter(country=country),
                "sites": Site.objects.filter(district__region__zone__country=country),
            })
        else:
            context.update({
                "is_site_only": True,
                "zones": Zone.objects.filter(id=site.district.region.zone.id),
                "sites": Site.objects.filter(id=site.id),
            })
        return context

    # Nurse & Clinician (own site only)
    if user.groups.filter(name__in=["NURSE", "CLINICIAN"]).exists():
        context.update({
            "is_site_only": True,
            "zones": Zone.objects.filter(id=site.district.region.zone.id),
            "sites": Site.objects.filter(id=site.id),
        })
        return context

    return context
