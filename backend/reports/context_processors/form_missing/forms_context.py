# reports/context_processors/forms_context.py

from django.apps import apps
from django.db.models import Exists, OuterRef
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def forms_report_total(request):
    """
    Computes counts of eligible screenings missing each major downstream form/stage.
    Visibility depends on user role:
      - Admin/Reviewer: all counts
      - Zonal lab: only missing_zonal_count
      - Others: enrollment, clinic, diagnosis, regimen (no zonal)
    """
    if not request.user.is_authenticated:
        return {
            "forms_report_total": {
                "missing_enrollment_count": 0,
                "missing_clinic_count":     0,
                "missing_diagnosis_count":  0,
                "missing_regimen_count":    0,
                "missing_zonal_count":      0,
                "total_form_missing":       0,
            }
        }

    # ── Get role context ───────────────────────────────────────
    role_context = get_role_context(request.user)
    is_zonal_lab = role_context.get("is_zonal_lab", False)
    is_admin     = role_context.get("is_admin", False)
    is_reviewer  = role_context.get("is_reviewer", False)
    is_superuser = request.user.is_superuser
    is_full_access = is_admin or is_superuser
    is_privileged = is_admin or is_reviewer

    # ── Models ─────────────────────────────────────────────────
    Screening        = apps.get_model("nanopore", "Screening")
    ClinicLaboratory = apps.get_model("nanopore", "ClinicLaboratory")
    Diagnosis        = apps.get_model("nanopore", "Diagnosis")
    RegimenChanges   = apps.get_model("nanopore", "RegimenChanges")
    ZonalLaboratory  = apps.get_model("nanopore", "ZonalLaboratory")

    # Base queryset (filtered by user permissions)
    screenings = Screening.objects.select_related(
        "site",
        "site__district__region__zone",
        "enrollment",
        "clinic_laboratory",
        "diagnosis",
        "zonal_laboratory",
    ).prefetch_related("regimen_changes")

    screenings = filter_queryset_by_user_role(
        request.user,
        screenings,
        site_field="site"
    )

    eligible_screenings = screenings.filter(eligible=True)

    # ───────────────────────────────────────────────────────────
    # Compute all counts (we'll selectively include them later)
    # ───────────────────────────────────────────────────────────

    # Missing enrollment
    missing_enrollment_count = eligible_screenings.filter(
        enrollment__isnull=True
    ).count()

    # Missing clinic lab
    missing_clinic_count = eligible_screenings.filter(
        clinic_laboratory__isnull=True
    ).count()

    # Missing diagnosis
    missing_diagnosis_count = eligible_screenings.filter(
        diagnosis__isnull=True
    ).count()

    # Missing regimen changes
    has_regimen_changes_subquery = RegimenChanges.objects.filter(
        screening=OuterRef("pk")
    )

    missing_regimen_qs = eligible_screenings.filter(
        ~Exists(has_regimen_changes_subquery),
        diagnosis__isnull=False,
        diagnosis__regimen_changed__name="Yes",
    )

    missing_regimen_count = missing_regimen_qs.distinct().count()

    # Missing zonal lab (only computed/returned for allowed roles)
    missing_zonal_count = 0
    if is_privileged or is_zonal_lab:
        missing_zonal_count = eligible_screenings.filter(
            clinic_laboratory__xpert_mtb_rif_conducted=1,
            clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
            zonal_laboratory__isnull=True
        ).count()

    # ───────────────────────────────────────────────────────────
    # Build total based on role
    # ───────────────────────────────────────────────────────────
    if is_privileged:
        # Admin / Reviewer: everything
        total_form_missing = (
            missing_enrollment_count +
            missing_clinic_count +
            missing_diagnosis_count +
            missing_regimen_count +
            missing_zonal_count
        )
    elif is_zonal_lab:
        # Zonal lab user: only zonal missing
        total_form_missing = missing_zonal_count
    else:
        # Normal users: upstream only (no zonal)
        total_form_missing = (
            missing_enrollment_count +
            missing_clinic_count +
            missing_diagnosis_count +
            missing_regimen_count
        )

    result = {
        "context_total_form_missing":       total_form_missing,
        "context_missing_enrollment_count": missing_enrollment_count,
        "context_missing_clinic_count":     missing_clinic_count,
        "context_missing_diagnosis_count":  missing_diagnosis_count,
        "context_missing_regimen_count":    missing_regimen_count,
        "context_missing_zonal_count":      missing_zonal_count,          # will be 0 for non-allowed users
    }

    return {"context_forms_report_total": result}