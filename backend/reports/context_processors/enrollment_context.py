# reports/context_processors/enrollment_context.py
from django.apps import apps
from utils.permissions import filter_queryset_by_user_role
from django.db.models import Count, Case, When, IntegerField, Q
from utils.roles import get_role_context

def enrollment_report_total(request):
    """
    Navbar count for Enrollment data quality issues.
    """

    if not request.user.is_authenticated:
        return {"enrollment_report_total": 0}

    Enrollment = apps.get_model("nanopore", "Enrollment")

    enrollments = Enrollment.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district",
        "screening__site__district__region",
        "screening__site__district__region__zone",
        "hiv_status",
        "other_diseases",
        "tb_regimen",
        "tb_category",
    )

    # Role context
    role_context = get_role_context(request.user)
    is_zonal_lab = role_context.get("is_zonal_lab", False)
    is_admin     = role_context.get("is_admin", False)
    is_reviewer  = role_context.get("is_reviewer", False)
    is_superuser = request.user.is_superuser
    is_full_access = is_admin or is_superuser
    is_privileged = is_admin or is_reviewer
    
    # ─────────────────────────────────────────────────────────────
    # Role-based filtering
    # ─────────────────────────────────────────────────────────────
    enrollments = filter_queryset_by_user_role(
        request.user,
        enrollments,
        site_field="screening__site",
    )

    # ─────────────────────────────────────────────────────────────
    # Optional UI filters
    # ─────────────────────────────────────────────────────────────
    # zone_id = request.GET.get("zone")
    # site_id = request.GET.get("site")

    # if zone_id:
    #     enrollments = enrollments.filter(
    #         screening__site__district__region__zone_id=zone_id
    #     )

    # if site_id:
    #     enrollments = enrollments.filter(
    #         screening__site_id=site_id
    #     )
        
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

    missing_diseases_medical = (
        enrollments
        .filter(other_diseases=1)
        .annotate(
            diseases_medical_count=Count("diseases_medical", distinct=True)
        )
        .filter(diseases_medical_count=0)
        .count()
    )

    missing_diseases_specify = enrollments.filter(
        diseases_medical__value=96,
        diseases_specify__isnull=True
    ).distinct().count()

    # =====================================================
    # TB TREATMENT FIELDS (simple null checks)
    # =====================================================
    missing_dr_ds = enrollments.filter(tx_previous=1,dr_ds__isnull=True).count()
    missing_tb_regimen = enrollments.filter(tx_previous=1,tb_regimen__isnull=True).count()
    missing_tb_outcome = enrollments.filter(tx_previous=1,tb_otcome__isnull=True).count()  # fixed typo

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
        tb_category__value=96,
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

        missing_dr_ds,
        missing_tb_regimen,
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

        "missing_dr_ds": missing_dr_ds,
        "missing_tb_regimen": missing_tb_regimen,
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
