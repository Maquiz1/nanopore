# utils/context_processors.py

from django.apps import apps
from django.db.models import Exists, OuterRef
from utils.permissions import filter_queryset_by_user_role


def forms_report_total(request):
    """
    Computes counts of eligible screenings missing each major downstream form/stage.
    """

    if not request.user.is_authenticated:
        return {
            "forms_report_total": {
                "missing_enrollment_count": 0,
                "missing_clinic_count":     0,
                "missing_diagnosis_count":  0,
                "missing_regimen_count":    0,
                "missing_zonal_count":      0,
                "total_missing":            0,
            }
        }

    Screening        = apps.get_model("nanopore", "Screening")
    ClinicLaboratory = apps.get_model("nanopore", "ClinicLaboratory")
    Diagnosis        = apps.get_model("nanopore", "Diagnosis")
    RegimenChanges   = apps.get_model("nanopore", "RegimenChanges")
    ZonalLaboratory  = apps.get_model("nanopore", "ZonalLaboratory")

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

    # ────────────────────────────────────────────────
    # Missing enrollment
    # ────────────────────────────────────────────────
    missing_enrollment_count = eligible_screenings.filter(
        enrollment__isnull=True
    ).count()

    # ────────────────────────────────────────────────
    # Missing clinic lab
    # ────────────────────────────────────────────────
    missing_clinic_count = eligible_screenings.filter(
        clinic_laboratory__isnull=True
    ).count()

    # ────────────────────────────────────────────────
    # Missing diagnosis
    # ────────────────────────────────────────────────
    missing_diagnosis_count = eligible_screenings.filter(
        diagnosis__isnull=True
    ).count()

    # ────────────────────────────────────────────────
    # ✅ Missing zonal lab — CORRECT RULE
    # ────────────────────────────────────────────────
    missing_zonal_count = eligible_screenings.filter(
        clinic_laboratory__xpert_mtb_rif_conducted=1,
        clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
        zonal_laboratory__isnull=True
    ).count()

    # ────────────────────────────────────────────────
    # Missing regimen changes
    # ────────────────────────────────────────────────
    has_regimen_changes_subquery = RegimenChanges.objects.filter(
        screening=OuterRef("pk")
    )

    missing_regimen_qs = eligible_screenings.filter(
        ~Exists(has_regimen_changes_subquery),
        diagnosis__isnull=False,
        diagnosis__regimen_changed__name="Yes",
    )

    missing_regimen_count = missing_regimen_qs.distinct().count()

    total_form_missing = (
        missing_enrollment_count +
        missing_clinic_count +
        missing_diagnosis_count +
        missing_regimen_count +
        missing_zonal_count
    )

    result = {
        "total_form_missing":       total_form_missing,
        "missing_enrollment_count": missing_enrollment_count,
        "missing_clinic_count":     missing_clinic_count,
        "missing_diagnosis_count":  missing_diagnosis_count,
        "missing_regimen_count":    missing_regimen_count,
        "missing_zonal_count":      missing_zonal_count,
    }

    return {"forms_report_total": result}
