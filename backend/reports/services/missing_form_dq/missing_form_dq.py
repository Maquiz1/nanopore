from django.apps import apps
from django.db.models import Exists, OuterRef
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def get_missing_forms_dq(user, zone_id=None, site_id=None, role=None):
    """
    Fully centralized missing form counts.
    Clean structure similar to get_specific_form_dq.
    """

    Screening = apps.get_model("nanopore", "Screening")
    RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

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

    # ───────────────────────────────────────────────────────────────
    # ── Missing Calculations Section (Structured like DQ) ─────────
    # ───────────────────────────────────────────────────────────────

    # ── Enrollment ──
    missing_enrollment_count = qs.filter(
        enrollment__isnull=True
    ).count()

    # ── Clinic ──
    missing_clinic_count = qs.filter(
        clinic_laboratory__isnull=True
    ).count()

    # ── Diagnosis ──
    missing_diagnosis_count = qs.filter(
        diagnosis__isnull=True
    ).count()

    # ── Regimen ──
    has_regimen_changes = RegimenChanges.objects.filter(
        screening=OuterRef("pk")
    )

    missing_regimen_count = qs.filter(
        ~Exists(has_regimen_changes),
        diagnosis__isnull=False,
        diagnosis__regimen_changed__name="Yes",
    ).distinct().count()

    # ── Zonal ──
    missing_zonal_count = qs.filter(
        clinic_laboratory__xpert_mtb_rif_conducted=1,
        clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
        zonal_laboratory__isnull=True,
    ).count()

    # ───────────────────────────────────────────────────────────────
    # ── Role-Based Total Calculation (Same Pattern as DQ) ─────────
    # ───────────────────────────────────────────────────────────────

    if role == "privileged":
        total_form_missing = (
            missing_enrollment_count +
            missing_clinic_count +
            missing_diagnosis_count +
            missing_regimen_count +
            missing_zonal_count
        )

    elif role == "zonal_lab":
        total_form_missing = missing_zonal_count

    else:  # normal users
        total_form_missing = (
            missing_enrollment_count +
            missing_clinic_count +
            missing_diagnosis_count +
            missing_regimen_count
        )

    # ───────────────────────────────────────────────────────────────

    return {
        "missing_enrollment_count": missing_enrollment_count,
        "missing_clinic_count": missing_clinic_count,
        "missing_diagnosis_count": missing_diagnosis_count,
        "missing_regimen_count": missing_regimen_count,
        "missing_zonal_count": missing_zonal_count,
        "total_form_missing": total_form_missing,
    }
