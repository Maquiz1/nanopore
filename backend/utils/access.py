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
DATA_MANAGER = "DATA_MANAGER"
STATISTICIAN = "STATISTICIAN"
REVIEWER = "REVIEWER"
COORDINATOR = "COORDINATOR"
ADMIN = "ADMIN"
ALL_ROLES = [NURSE, CLINICIAN, LABORATORY_TECHNICIAN, DATA_SPECIALIST, DATA_MANAGER, STATISTICIAN, REVIEWER, COORDINATOR, ADMIN]

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
EXPORTS = "exports"            # data exports (CSV / XLSX of form data): data specialists, data managers, statisticians, admins
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
    DATA_MANAGER: ALL_FORMS,
    REVIEWER: frozenset(),
    ADMIN: ALL_FORMS,
}
# Read-only access on top of the editable forms.
ROLE_FORMS_VIEW = {
    LABORATORY_TECHNICIAN: frozenset([SCREENING]),  # look up a participant / PID
    REVIEWER: ALL_FORMS,
    STATISTICIAN: ALL_FORMS,
}
ROLE_FEATURES = {
    DATA_SPECIALIST: frozenset([REPORTS, EXPORTS, TBLIS_UPLOAD, SNAPSHOTS]),
    DATA_MANAGER: frozenset([REPORTS, EXPORTS, TBLIS_UPLOAD, SNAPSHOTS]),
    COORDINATOR: frozenset([SNAPSHOTS]),  # query trends of the zones/sites they are assigned
    STATISTICIAN: frozenset([REPORTS, EXPORTS, SNAPSHOTS]),
    REVIEWER: frozenset([REPORTS, SNAPSHOTS]),
    ADMIN: frozenset([REPORTS, EXPORTS, MODEL_EXPORT, SNAPSHOTS, SYSTEM_ADMIN, TBLIS_UPLOAD, DELETE_RECORDS]),
}
UNSCOPED_ROLES = frozenset([ADMIN, REVIEWER])
# Data managers and statisticians export every site, whatever their assignment
# (their pages still follow their assignment).
ALL_SITES_EXPORT_ROLES = frozenset([DATA_MANAGER, STATISTICIAN])


# New screenings: these roles pick the zone and site from a list; everyone else
# (nurses, clinicians) screens at the sites they are assigned to.
CHOOSE_SCREENING_SITE_ROLES = frozenset([ADMIN, DATA_MANAGER, DATA_SPECIALIST])


def chooses_screening_site(user):
    return bool(getattr(user, "is_superuser", False)) or has_role(user, *CHOOSE_SCREENING_SITE_ROLES)


def screening_site_choices(user):
    """Sites a new screening can be recorded at: active clinics (not the national lab) the user may see."""
    sites = Site.objects.filter(is_active=True).exclude(site_level__code__iexact="national")
    accessible = get_accessible_sites(user)
    if accessible is not None:
        sites = sites.filter(pk__in=accessible)
    return sites.select_related("district__region__zone").order_by("district__region__zone__name", "name")


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
        # A position can also give its role (accounts set up with a position but no group).
        profile = getattr(user, "profile", None)
        position = profile.position.name.strip().lower() if profile and profile.position else ""
        if position == "data specialist":
            roles.add(DATA_SPECIALIST)
        elif position == "coordinator":
            roles.add(COORDINATOR)
        elif position == "data manager":
            roles.add(DATA_MANAGER)
        elif position.startswith("statist"):  # also the misspelt "Statistiician" position
            roles.add(STATISTICIAN)
        elif position == "reviewer":
            roles.add(REVIEWER)
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
    Data-quality queries go to whoever can fix them (edit rights), plus reviewers and
    statisticians, who see every form's queries (statisticians for their assigned sites).
    Read-only lookups (lab technicians on Screening) don't bring the queries along.
    """
    return can_edit(user, form) or has_role(user, REVIEWER, STATISTICIAN)


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


def exports_all_sites(user):
    return is_unscoped(user) or has_role(user, *ALL_SITES_EXPORT_ROLES)


def export_queryset(user, qs, site_field="site"):
    """Records a data export may contain: every site for admins, data managers and statisticians."""
    return qs if exports_all_sites(user) else scope_queryset(user, qs, site_field)


def get_accessible_zones(user):
    sites = get_accessible_sites(user)
    if sites is None:
        return Zone.objects.all()
    return Zone.objects.filter(region__district__site__in=sites).distinct()


def legacy_role_flags(user):
    """Template flags used by the form-status and master-data lists."""
    is_admin_only = bool(getattr(user, "is_superuser", False)) or has_role(user, ADMIN, DATA_SPECIALIST, DATA_MANAGER)
    is_reviewer = has_role(user, REVIEWER, STATISTICIAN)
    return {
        "is_admin_or_reviewer": is_admin_only or is_reviewer,
        "is_admin_only": is_admin_only,
        "is_reviewer_only": is_reviewer and not is_admin_only,
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
