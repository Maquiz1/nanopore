from django.apps import apps
from django.db.models import Exists, OuterRef
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def get_missing_forms_counts(user, zone_id=None, site_id=None):
    """
    Returns role-aware missing form counts for dashboards & detail views.
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
    if is_privileged or is_zonal_lab:
        missing_zonal_count = qs.filter(
            clinic_laboratory__xpert_mtb_rif_conducted=1,
            clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
            zonal_laboratory__isnull=True,
        ).count()

    # ── Total (role-aware) ─────────────────────────────────────────
    if is_privileged:
        total_form_missing = (
            missing_enrollment_count +
            missing_clinic_count +
            missing_diagnosis_count +
            missing_regimen_count +
            missing_zonal_count
        )
    elif is_zonal_lab:
        total_form_missing = missing_zonal_count
    else:
        total_form_missing = (
            missing_enrollment_count +
            missing_clinic_count +
            missing_diagnosis_count +
            missing_regimen_count
        )

    return {
        "missing_enrollment_count": missing_enrollment_count,
        "missing_clinic_count": missing_clinic_count,
        "missing_diagnosis_count": missing_diagnosis_count,
        "missing_regimen_count": missing_regimen_count,
        "missing_zonal_count": missing_zonal_count,
        "total_form_missing": total_form_missing,
    }
