# utils/context_processors.py
from django.apps import apps
from django.db.models import Exists, OuterRef, Q,F
from utils.permissions import filter_queryset_by_user_role


def forms_report_total(request):
    """
    Computes counts of eligible screenings missing each major downstream form/stage.
    
    Returns nested dictionary under "forms_report_total" so existing templates
    continue to work without changes.
    
    Missing forms are only counted for screenings where:
    - eligible = True
    - the user has permission to see the screening (via filter_queryset_by_user_role)
    
    Special rule for regimen changes:
      - Only considered "missing" when Diagnosis.regimen_changed == Yes
        AND no RegimenChanges records exist for that screening.
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

    # ── Load models dynamically ─────────────────────────────────────────────
    Screening       = apps.get_model("nanopore", "Screening")
    ClinicLaboratory = apps.get_model("nanopore", "ClinicLaboratory")
    Diagnosis       = apps.get_model("nanopore", "Diagnosis")
    RegimenChanges  = apps.get_model("nanopore", "RegimenChanges")
    ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")

    # ── Base queryset: all screenings the current user is allowed to see ────
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

    # ── Only eligible screenings are considered for quality issues ──────────
    eligible_screenings = screenings.filter(eligible=True)

    # ── 1. Missing Enrollment ───────────────────────────────────────────────
    missing_enrollment_count = eligible_screenings.filter(
        enrollment__isnull=True
    ).count()

    # ── 2. Missing Clinic Laboratory ───────────────────────────────────────
    missing_clinic_count = eligible_screenings.filter(
        clinic_laboratory__isnull=True
    ).count()

    # ── 3. Missing Diagnosis ────────────────────────────────────────────────
    missing_diagnosis_count = eligible_screenings.filter(
        diagnosis__isnull=True
    ).count()

    # ── 4. Missing Zonal Laboratory ────────────────────────────────────────
    missing_zonal_count = eligible_screenings.filter(
        zonal_laboratory__isnull=True
    ).count()

    # ── 5. Missing Regimen Changes ──────────────────────────────────────────
    # Only screenings where regimen change was indicated (Yes),
    # but no actual change records were created.
    has_regimen_changes_subquery = RegimenChanges.objects.filter(
        screening=OuterRef("pk")
    )

    missing_regimen_qs = eligible_screenings.filter(
        ~Exists(has_regimen_changes_subquery),           # ← positional Q object first
        diagnosis__isnull=False,
        diagnosis__regimen_changed__name="Yes",          # ← keywords after
    )

    missing_regimen_count = missing_regimen_qs.distinct().count()

    # ── Total missing forms (simple sum – one count per missing form type) ──
    total_form_missing = (
        missing_enrollment_count +
        missing_clinic_count +
        missing_diagnosis_count +
        missing_regimen_count +
        missing_zonal_count
    )

    # ── Final result structure (matches your dashboard template) ─────────────
    result = {
        "total_form_missing":       total_form_missing,
        "missing_enrollment_count": missing_enrollment_count,
        "missing_clinic_count":     missing_clinic_count,
        "missing_diagnosis_count":  missing_diagnosis_count,
        "missing_regimen_count":    missing_regimen_count,
        "missing_zonal_count":      missing_zonal_count,
    }

    return {"forms_report_total": result}