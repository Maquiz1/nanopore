"""
Zonal Lab data entry rules.

Dar es Salaam (CTRL) zonal labs report their results through TBLIS: the TBLIS
upload merges them into the EDCS/TBLIS record by lab number. So for Dar es Salaam
participants the Zonal Lab form only takes the Unique Lab Number; every other
zone enters the full form.
"""
from django.db.models import Q

LAB_NUMBER_ONLY_ZONE = "dar es salaam"

# Zonal Lab records of lab-number-only participants.
LAB_NUMBER_ONLY_Q = Q(screening__site__district__region__zone__name__iexact=LAB_NUMBER_ONLY_ZONE)


def is_lab_number_only(screening):
    """True when this participant's Zonal Lab form only takes the Unique Lab Number."""
    site = getattr(screening, "site", None)
    region = getattr(getattr(site, "district", None), "region", None)
    zone = getattr(region, "zone", None)
    return bool(zone and zone.name.strip().lower() == LAB_NUMBER_ONLY_ZONE)
