# reports/context_processors.py

from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role


def enrollment_report_total(request):
    """
    Navbar count for Enrollment data quality issues.

    Rules implemented:

    ---------------------------------------------------
    BASIC MISSING CHECKS
    ---------------------------------------------------
    - hiv_status
    - other_diseases / diseases_medical / diseases_specify
    - sputum_collected / sputum_date / sputum_reasons

    ---------------------------------------------------
    TREATMENT DATA
    ---------------------------------------------------
    - tx_year
    - dr_ds
    - ltf_months / ltf_months_unknown
    - tb_regimen / tb_regimen_specify
    - tb_category / tb_category_specify
    - regimen_months / regimen_months_unknown
    - tb_outcome

    ---------------------------------------------------
    PREVIOUS TREATMENT LOGIC (tx_previous = 1)
    ---------------------------------------------------

    Required:
        - tx_month OR tx_unknown_month = True
        - tx_year  OR tx_unknown_year  = True
        - regimen_months OR regimen_months_unknown = True

    Rules:
        • If tx_month is missing → tx_unknown_month MUST be True
        • If tx_unknown_month is True → tx_month must be NULL or 99
        • If tx_year is missing → tx_unknown_year MUST be True
        • If tx_unknown_year is True:
              - tx_year must be NULL or 99
              - tx_month must be NULL or 99
              - tx_unknown_month MUST be True
        • If regimen_months is missing → regimen_months_unknown MUST be True
        • If regimen_months_unknown is True → regimen_months must be NULL
        • If tb_regimen=8 → tb_regimen_specify MUST NOT be NULL
        • If tb_regimen=96 → tb_regimen_specify MUST NOT be NULL
        • If tb_category=96 → tb_category_specify MUST NOT be NULL
        • If tb_category=2 or 3 → 
              - ltf_months MUST NOT be NULL and ltf_months_unknown=False
              OR
              - ltf_months IS NULL and ltf_months_unknown=True
        • If sputum_collected=1 → sputum_date MUST NOT be NULL
        • If sputum_collected=2 → sputum_reasons MUST NOT be NULL
        • If other_diseases=1 → diseases_medical MUST NOT be NULL
        • If diseases_medical=96 → diseases_specify MUST NOT be NULL
    """

    if not request.user.is_authenticated:
        return {"enrollment_report_total": 0}

    Enrollment = apps.get_model("nanopore", "Enrollment")

    enrollments = Enrollment.objects.all()
    enrollments = filter_queryset_by_user_role(request.user, enrollments, site_field="screening__site")

    # =====================================================
    # BASIC REQUIRED FIELDS
    # =====================================================

    missing_hiv_status = enrollments.filter(hiv_status__isnull=True).count()
    missing_other_diseases = enrollments.filter(other_diseases__isnull=True).count()
    missing_sputum_collected = enrollments.filter(sputum_collected__isnull=True).count()

    # -----------------------------------------------------
    # Sputum conditional checks
    # -----------------------------------------------------
    missing_sputum_date = enrollments.filter(
        sputum_collected=1,
        sputum_date__isnull=True
    ).count()

    missing_sputum_reasons = enrollments.filter(
        sputum_collected=2,
        sputum_reasons__isnull=True
    ).count()

    # -----------------------------------------------------
    # Other diseases conditional checks
    # -----------------------------------------------------
    missing_diseases_medical = enrollments.filter(
        other_diseases=1,
        diseases_medical__isnull=True
    ).count()

    # diseases_medical = 96 requires diseases_specify
    missing_diseases_specify = enrollments.filter(
        diseases_medical=96,
        diseases_specify__isnull=True
    ).count()

    # =====================================================
    # TB TREATMENT FIELDS
    # =====================================================

    missing_tx_year = enrollments.filter(tx_year__isnull=True).count()
    missing_dr_ds = enrollments.filter(dr_ds__isnull=True).count()
    missing_ltf_months = enrollments.filter(regimen_months__isnull=True).count()
    missing_tb_regimen = enrollments.filter(tb_regimen__isnull=True).count()
    missing_regimen_months = enrollments.filter(regimen_months__isnull=True).count()
    missing_tb_outcome = enrollments.filter(tb_otcome__isnull=True).count()

    # TB Regimen = Other (96) requires specification
    missing_tb_regimen_specify = enrollments.filter(
        tb_regimen__value=96,
        tb_regimen_specify__isnull=True
    ).count()

    # TB Regimen = 8 requires tb_regimen_specify
    missing_tb_regimen_specify_8 = enrollments.filter(
        tb_regimen=8,
        tb_regimen_specify__isnull=True
    ).count()

    # TB Category = 96 requires tb_category_specify
    missing_tb_category_specify = enrollments.filter(
        tb_category=96,
        tb_category_specify__isnull=True
    ).count()

    # TB Category = 2 or 3 requires ltf_months logic
    invalid_ltf_months = enrollments.filter(
        tb_category__in=[2, 3]
    ).exclude(
        Q(ltf_months__isnull=False, ltf_months_unknown=False) |
        Q(ltf_months__isnull=True, ltf_months_unknown=True)
    ).count()

    # =====================================================
    # PREVIOUS TB TREATMENT LOGIC
    # =====================================================

    previous_tx = enrollments.filter(tx_previous=1)

    missing_tx_month_without_unknown = previous_tx.filter(
        tx_month__isnull=True,
        tx_unknown_month=False
    ).count()

    invalid_tx_month_with_unknown = previous_tx.filter(
        tx_unknown_month=True
    ).exclude(Q(tx_month__isnull=True) | Q(tx_month=99)).count()

    missing_tx_year_without_unknown = previous_tx.filter(
        tx_year__isnull=True,
        tx_unknown_year=False
    ).count()

    invalid_tx_year_with_unknown = previous_tx.filter(
        tx_unknown_year=True
    ).exclude(Q(tx_year__isnull=True) | Q(tx_year=99)).count()

    invalid_unknown_year_dependencies = previous_tx.filter(
        tx_unknown_year=True
    ).exclude(Q(tx_month__isnull=True) | Q(tx_month=99), tx_unknown_month=True).count()

    missing_regimen_months_without_unknown = previous_tx.filter(
        regimen_months__isnull=True,
        regimen_months_unknown=False
    ).count()

    invalid_regimen_months_with_unknown = previous_tx.filter(
        regimen_months_unknown=True
    ).exclude(Q(regimen_months__isnull=True)).count()

    # =====================================================
    # TOTAL ISSUES
    # =====================================================

    enrollment_report_total = sum([
        missing_hiv_status,
        missing_other_diseases,
        missing_sputum_collected,
        missing_sputum_date,
        missing_sputum_reasons,
        missing_diseases_medical,
        missing_diseases_specify,

        missing_tx_year,
        missing_dr_ds,
        missing_ltf_months,
        missing_tb_regimen,
        missing_regimen_months,
        missing_tb_outcome,

        missing_tb_regimen_specify,
        missing_tb_regimen_specify_8,
        missing_tb_category_specify,
        invalid_ltf_months,

        missing_tx_month_without_unknown,
        invalid_tx_month_with_unknown,
        missing_tx_year_without_unknown,
        invalid_tx_year_with_unknown,
        invalid_unknown_year_dependencies,

        missing_regimen_months_without_unknown,
        invalid_regimen_months_with_unknown,
    ])

    return {
        "enrollment_report_total": enrollment_report_total,

        # breakdown
        "missing_hiv_status": missing_hiv_status,
        "missing_other_diseases": missing_other_diseases,
        "missing_sputum_collected": missing_sputum_collected,
        "missing_sputum_date": missing_sputum_date,
        "missing_sputum_reasons": missing_sputum_reasons,
        "missing_diseases_medical": missing_diseases_medical,
        "missing_diseases_specify": missing_diseases_specify,

        "missing_tx_year": missing_tx_year,
        "missing_dr_ds": missing_dr_ds,
        "missing_ltf_months": missing_ltf_months,
        "missing_tb_regimen": missing_tb_regimen,
        "missing_regimen_months": missing_regimen_months,
        "missing_tb_outcome": missing_tb_outcome,

        "missing_tb_regimen_specify": missing_tb_regimen_specify,
        "missing_tb_regimen_specify_8": missing_tb_regimen_specify_8,
        "missing_tb_category_specify": missing_tb_category_specify,
        "invalid_ltf_months": invalid_ltf_months,

        "missing_tx_month_without_unknown": missing_tx_month_without_unknown,
        "invalid_tx_month_with_unknown": invalid_tx_month_with_unknown,
        "missing_tx_year_without_unknown": missing_tx_year_without_unknown,
        "invalid_tx_year_with_unknown": invalid_tx_year_with_unknown,
        "invalid_unknown_year_dependencies": invalid_unknown_year_dependencies,

        "missing_regimen_months_without_unknown": missing_regimen_months_without_unknown,
        "invalid_regimen_months_with_unknown": invalid_regimen_months_with_unknown,
    }
