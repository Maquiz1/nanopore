from nanopore.substudy import SUBSTUDY_2, substudy_q
from utils import access
from utils.access import can_view, visible_missing_total
from django.apps import apps
from django.db.models import Exists, OuterRef
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def get_missing_forms_counts(user, zone_id=None, site_id=None, screened_before=None):
    """
    Returns role-aware missing form counts for dashboards & detail views.
    screened_before: only participants screened before that date (the dashboard's "waiting over 30 days").
    """

    Screening = apps.get_model("nanopore", "Screening")
    RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

    # ── Role context ───────────────────────────────────────────────
    role_context = get_role_context(user)
    is_admin     = role_context.get("is_admin", False)
    is_reviewer  = role_context.get("is_reviewer", False)
    is_zonal_lab = role_context.get("is_zonal_lab", False)
    is_superuser = user.is_superuser
    is_privileged = is_admin or is_reviewer or is_superuser

    # ── Base queryset (role-filtered) ──────────────────────────────
    qs = Screening.objects.select_related(
        "site",
        "site__district__region__zone",
        "enrollment",
        "clinic_laboratory",
        "diagnosis",
        "zonal_laboratory",
    ).prefetch_related("regimen_changes")

    qs = filter_queryset_by_user_role(user, qs, site_field="site")
    qs = qs.filter(eligible=True)

    # ── Zone / Site filters ────────────────────────────────────────
    if zone_id:
        qs = qs.filter(site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(site_id=site_id)
    if screened_before:
        qs = qs.filter(screening_date__lt=screened_before)

    # ── Missing counts ─────────────────────────────────────────────
    missing_enrollment_count = qs.filter(enrollment__isnull=True).count()
    missing_clinic_count     = qs.filter(clinic_laboratory__isnull=True).count()
    missing_diagnosis_count  = qs.filter(diagnosis__isnull=True).count()

    has_regimen_changes = RegimenChanges.objects.filter(screening=OuterRef("pk"))
    missing_regimen_count = qs.filter(
        ~Exists(has_regimen_changes),
        diagnosis__isnull=False,
        diagnosis__regimen_changed__name="Yes",
    ).distinct().count()

    missing_zonal_count = 0
    if can_view(user, access.ZONAL_LAB):
        missing_zonal_count = qs.filter(
            substudy_q(SUBSTUDY_2),
            zonal_laboratory__isnull=True,
        ).count()

    # ── Total (role-aware) ─────────────────────────────────────────
    total_form_missing = visible_missing_total(user, {
        "enrollment": missing_enrollment_count,
        "clinic": missing_clinic_count,
        "diagnosis": missing_diagnosis_count,
        "regimen": missing_regimen_count,
        "zonal": missing_zonal_count,
    })

    # A form closed to new records (System Controls) has nothing missing
    from nanopore.study_lock import closed_forms
    from utils.access import MISSING_FORM_TYPES
    closed = {key for key, form in MISSING_FORM_TYPES.items() if form in closed_forms()}
    missing_enrollment_count = 0 if "enrollment" in closed else missing_enrollment_count
    missing_clinic_count = 0 if "clinic" in closed else missing_clinic_count
    missing_diagnosis_count = 0 if "diagnosis" in closed else missing_diagnosis_count
    missing_regimen_count = 0 if "regimen" in closed else missing_regimen_count
    missing_zonal_count = 0 if "zonal" in closed else missing_zonal_count
    return {
        "missing_enrollment_count": missing_enrollment_count,
        "missing_clinic_count": missing_clinic_count,
        "missing_diagnosis_count": missing_diagnosis_count,
        "missing_regimen_count": missing_regimen_count,
        "missing_zonal_count": missing_zonal_count,
        "total_form_missing": total_form_missing,
    }
