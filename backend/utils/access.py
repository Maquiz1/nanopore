# utils/access.py
"""
Single source of truth for who can see and change what.

Two independent questions are answered here:

1. WHICH FORMS a user may view / edit  -> decided by their roles (groups).
   A user may hold several roles; their rights are the union of all of them.

2. WHICH RECORDS a user may see        -> decided by their assignment (Profile).
   * Zones assigned  -> every site inside those zones. Zone assignment
                        overrides any site assignment.
   * Sites only      -> exactly those sites. For LABORATORY_TECHNICIAN a
                        zonal-level lab site widens to its whole zone, and a
                        national-level lab site to its whole country, because
                        lab records belong to the clinic that screened the
                        participant, not to the lab.
   * ADMIN, REVIEWER and superusers are not limited by assignment.
"""
from django.db.models import Q

from locations.models import Site, Zone

# --- Roles (Django group names) ---
NURSE = "NURSE"
CLINICIAN = "CLINICIAN"
LABORATORY_TECHNICIAN = "LABORATORY_TECHNICIAN"
DATA_SPECIALIST = "DATA_SPECIALIST"
REVIEWER = "REVIEWER"
ADMIN = "ADMIN"
ALL_ROLES = [NURSE, CLINICIAN, LABORATORY_TECHNICIAN, DATA_SPECIALIST, REVIEWER, ADMIN]

# --- Forms ---
SCREENING = "screening"
ENROLLMENT = "enrollment"
CLINIC_LAB = "clinic_lab"
ZONAL_LAB = "zonal_lab"
EDCS_TBLIS = "edcs_tblis"
DIAGNOSIS = "diagnosis"
REGIMEN = "regimen"
ALL_FORMS = frozenset([SCREENING, ENROLLMENT, CLINIC_LAB, ZONAL_LAB, EDCS_TBLIS, DIAGNOSIS, REGIMEN])
CLINICAL_FORMS = frozenset([SCREENING, ENROLLMENT, CLINIC_LAB, DIAGNOSIS, REGIMEN])
LAB_FORMS = frozenset([ZONAL_LAB, EDCS_TBLIS])

# --- Features (pages that are not a single form) ---
REPORTS = "reports"            # summary reports, records lists, substudy pages
EXPORTS = "exports"            # CSV / XLSX downloads of form data
MODEL_EXPORT = "model_export"  # raw "export all models" tools
SNAPSHOTS = "snapshots"        # data-quality snapshot dashboards
SYSTEM_ADMIN = "system_admin"  # system controls, locations, targets, admin site
TBLIS_UPLOAD = "tblis_upload"  # TBLIS raw upload
BULK_UPLOAD = "bulk_upload"    # CSV imports of whole forms (superusers only: no role grants it)
DELETE_RECORDS = "delete_records"  # delete form records to the recycle bin, and restore them

ROLE_FORMS_EDIT = {
    NURSE: CLINICAL_FORMS,
    CLINICIAN: CLINICAL_FORMS,
    LABORATORY_TECHNICIAN: LAB_FORMS,
    DATA_SPECIALIST: ALL_FORMS,
    REVIEWER: frozenset(),
    ADMIN: ALL_FORMS,
}
# Read-only access on top of the editable forms.
ROLE_FORMS_VIEW = {
    LABORATORY_TECHNICIAN: frozenset([SCREENING]),  # look up a participant / PID
    REVIEWER: ALL_FORMS,
}
ROLE_FEATURES = {
    DATA_SPECIALIST: frozenset([REPORTS, EXPORTS, TBLIS_UPLOAD]),
    REVIEWER: frozenset([REPORTS, EXPORTS]),
    ADMIN: frozenset([REPORTS, EXPORTS, MODEL_EXPORT, SNAPSHOTS, SYSTEM_ADMIN, TBLIS_UPLOAD, DELETE_RECORDS]),
}
UNSCOPED_ROLES = frozenset([ADMIN, REVIEWER])


def _cache(user):
    """Per-request cache stored on the user object (users are re-fetched every request)."""
    cache = getattr(user, "_access_cache", None)
    if cache is None:
        cache = {}
        try:
            user._access_cache = cache
        except AttributeError:
            pass
    return cache


def get_user_roles(user):
    if not getattr(user, "is_authenticated", False):
        return frozenset()
    cache = _cache(user)
    if "roles" not in cache:
        roles = {name.upper() for name in user.groups.values_list("name", flat=True)}
        # Legacy: data specialists used to be identified by Profile.position.
        profile = getattr(user, "profile", None)
        if profile and profile.position and profile.position.name.strip().lower() == "data specialist":
            roles.add(DATA_SPECIALIST)
        cache["roles"] = frozenset(roles)
    return cache["roles"]


def has_role(user, *roles):
    return bool(get_user_roles(user) & set(roles))


def is_unscoped(user):
    return bool(getattr(user, "is_superuser", False)) or has_role(user, *UNSCOPED_ROLES)


def can_edit(user, form):
    if getattr(user, "is_superuser", False):
        return True
    return any(form in ROLE_FORMS_EDIT.get(role, ()) for role in get_user_roles(user))


def can_view(user, form):
    if can_edit(user, form):
        return True
    return any(form in ROLE_FORMS_VIEW.get(role, ()) for role in get_user_roles(user))


def can_see_queries(user, form):
    """
    Data-quality queries go to whoever can fix them (edit rights), plus reviewers.
    Read-only lookups (lab technicians on Screening) don't bring the queries along.
    """
    return can_edit(user, form) or has_role(user, REVIEWER)


def has_feature(user, feature):
    if getattr(user, "is_superuser", False):
        return True
    return any(feature in ROLE_FEATURES.get(role, ()) for role in get_user_roles(user))


def get_accessible_sites(user):
    """Sites whose records the user may see. None means "all sites" (unscoped)."""
    if is_unscoped(user):
        return None
    cache = _cache(user)
    if "site_ids" not in cache:
        cache["site_ids"] = _compute_site_ids(user)
    return Site.objects.filter(id__in=cache["site_ids"])


def _compute_site_ids(user):
    profile = getattr(user, "profile", None)
    if not getattr(user, "is_authenticated", False) or profile is None or not get_user_roles(user):
        return []

    zone_ids = list(profile.zones.values_list("id", flat=True))
    if zone_ids:
        # Zone assignment overrides site assignment.
        return list(Site.objects.filter(district__region__zone_id__in=zone_ids).values_list("id", flat=True))

    sites = profile.sites.select_related("site_level", "district__region__zone")
    widen_lab_sites = has_role(user, LABORATORY_TECHNICIAN)
    q = Q(pk__in=[])
    for site in sites:
        level = site.site_level.code.lower() if site.site_level else ""
        zone = site.district.region.zone if site.district and site.district.region else None
        if widen_lab_sites and level == "zonal" and zone:
            q |= Q(district__region__zone=zone)
        elif widen_lab_sites and level == "national" and zone:
            q |= Q(district__region__zone__country_id=zone.country_id)
        else:
            q |= Q(pk=site.pk)
    return list(Site.objects.filter(q).values_list("id", flat=True))


def scope_queryset(user, qs, site_field="site"):
    """Limit qs to the records of the sites the user is assigned to."""
    sites = get_accessible_sites(user)
    if sites is None:
        return qs
    return qs.filter(**{f"{site_field}__in": sites})


def get_accessible_zones(user):
    sites = get_accessible_sites(user)
    if sites is None:
        return Zone.objects.all()
    return Zone.objects.filter(region__district__site__in=sites).distinct()


def legacy_role_flags(user):
    """Template flags used by the form-status and master-data lists."""
    is_admin_only = bool(getattr(user, "is_superuser", False)) or has_role(user, ADMIN, DATA_SPECIALIST)
    return {
        "is_admin_or_reviewer": is_admin_only or has_role(user, REVIEWER),
        "is_admin_only": is_admin_only,
        "is_reviewer_only": has_role(user, REVIEWER) and not is_admin_only,
        "is_lab_tech": has_role(user, LABORATORY_TECHNICIAN),
        "is_nurse_clinician": has_role(user, NURSE, CLINICIAN),
    }


# Missing-form keys used by the data-quality pages -> form they belong to.
MISSING_FORM_TYPES = {
    "enrollment": ENROLLMENT,
    "clinic": CLINIC_LAB,
    "diagnosis": DIAGNOSIS,
    "regimen": REGIMEN,
    "zonal": ZONAL_LAB,
}


def visible_missing_total(user, counts):
    """Sum of missing-form counts ({"enrollment": n, ...}) for the forms the user can view."""
    return sum(n for key, n in counts.items() if can_see_queries(user, MISSING_FORM_TYPES[key]))


def assigned_locations(user):
    """Zones and sites to show as the user's assignment (zones override sites)."""
    profile = getattr(user, "profile", None)
    if profile is None:
        return [], []
    zones = list(profile.zones.all())
    if zones:
        sites = Site.objects.filter(district__region__zone__in=zones)
    else:
        sites = profile.sites.all()
    return zones, sorted(sites, key=lambda site: site.name)


class AccessFlags:
    """Template helper: {{ access.view.zonal_lab }}, {{ access.edit.screening }}, {{ access.reports }}."""

    class _Lookup:
        def __init__(self, user, check):
            self._user, self._check = user, check

        def __getitem__(self, form):
            return self._check(self._user, form)

        __getattr__ = __getitem__

    def __init__(self, user):
        self.user = user
        self.view = self._Lookup(user, can_view)
        self.edit = self._Lookup(user, can_edit)
        self.queries = self._Lookup(user, can_see_queries)
        self.roles = get_user_roles(user)
        self.is_admin = bool(getattr(user, "is_superuser", False)) or ADMIN in self.roles
        self.is_unscoped = is_unscoped(user)

    def __getattr__(self, feature):
        if feature.startswith("_"):
            raise AttributeError(feature)
        return has_feature(self.user, feature)
