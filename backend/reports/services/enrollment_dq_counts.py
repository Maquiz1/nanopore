# reports/services/enrollment_dq_counts.py
from django.apps import apps
from django.db.models import Count, Q
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

def get_enrollment_dq_counts(user, zone_id=None, site_id=None):
    Enrollment = apps.get_model("nanopore", "Enrollment")
    qs = Enrollment.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district__region__zone",
        "hiv_status",
        "other_diseases",
        "tb_regimen",
        "tb_category",
    ).prefetch_related("diseases_medical")

    qs = filter_queryset_by_user_role(user, qs, site_field="screening__site")

    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(screening__site_id=site_id)

    # Role context for full access
    role_context = get_role_context(user)
    is_admin = role_context.get("is_admin", False)
    is_superuser = user.is_superuser
    is_full_access = is_admin or is_superuser

    # BASIC REQUIRED FIELDS
    missing_hiv_status = qs.filter(hiv_status__isnull=True).count()
    missing_other_diseases = qs.filter(other_diseases__isnull=True).count()
    missing_sputum_collected = qs.filter(sputum_collected__isnull=True).count()
    missing_sputum_date = qs.filter(sputum_collected=1, sputum_date__isnull=True).count()
    missing_sputum_reasons = qs.filter(sputum_collected=2, sputum_reasons__isnull=True).count()

    missing_diseases_medical = (
        qs.filter(other_diseases=1)
        .annotate(diseases_medical_count=Count("diseases_medical", distinct=True))
        .filter(diseases_medical_count=0)
        .count()
    )

    missing_diseases_specify = qs.filter(diseases_medical__value=96, diseases_specify__isnull=True).distinct().count()

    # TB treatment
    missing_dr_ds = qs.filter(tx_previous=1, dr_ds__isnull=True).count()
    missing_tb_regimen = qs.filter(tx_previous=1, tb_regimen__isnull=True).count()
    missing_tb_outcome = qs.filter(tx_previous=1, tb_otcome__isnull=True).count()
    missing_tb_regimen_specify = qs.filter(tb_regimen__value=96, tb_regimen_specify__isnull=True).count()
    missing_tb_regimen_specify_8 = qs.filter(tb_regimen=8, tb_regimen_specify__isnull=True).count()
    missing_tb_category_specify = qs.filter(tb_category__value=96, tb_category_specify__isnull=True).count()

    invalid_ltf_months = qs.filter(
        tb_category__in=[2, 3]
    ).exclude(
        Q(ltf_months__isnull=False, ltf_months_unknown=False) |
        Q(ltf_months__isnull=True, ltf_months_unknown=True)
    ).count()

    # Previous TB treatment
    previous_tx = qs.filter(tx_previous=1)

    missing_tx_month_without_unknown = previous_tx.filter(tx_month__isnull=True, tx_unknown_month=False).count()
    invalid_tx_month_with_unknown = previous_tx.filter(tx_unknown_month=True).exclude(Q(tx_month__isnull=True) | Q(tx_month=99)).count()
    missing_tx_year_without_unknown = previous_tx.filter(tx_year__isnull=True, tx_unknown_year=False).count()
    invalid_tx_year_with_unknown = previous_tx.filter(tx_unknown_year=True).exclude(Q(tx_year__isnull=True) | Q(tx_year=99)).count()
    invalid_unknown_year_dependencies = previous_tx.filter(tx_unknown_year=True).exclude(Q(tx_month__isnull=True) | Q(tx_month=99), tx_unknown_month=True).count()

    missing_regimen_months_without_unknown = previous_tx.filter(regimen_months__isnull=True, regimen_months_unknown=False).count()
    invalid_regimen_months_with_unknown = previous_tx.filter(regimen_months_unknown=True).exclude(regimen_months__isnull=True).count()

# ─────────────────────────────────────────────
    # tx_previous = 2 or 3 → TB must be empty AND unknown flags must be False
    # ─────────────────────────────────────────────

    tx_previous_2_3_q = Q(tx_previous__in=[2, 3])

    tb_fields_filled_q = Q()

    # Char fields (can contain "")
    char_fields = [
        "tb_category_specify",
        "tb_regimen_specify",
    ]

    for field in char_fields:
        tb_fields_filled_q |= (
            ~Q(**{f"{field}__isnull": True}) &
            ~Q(**{f"{field}": ""})
        )

    # Numeric / FK /Date fields (only check NOT NULL)
    non_char_fields = [
        "tb_category",
        "tx_month",
        "tx_year",
        "dr_ds",
        "ltf_months",
        "tb_regimen",
        "regimen_months",
        "tb_otcome"
    ]

    for field in non_char_fields:
        tb_fields_filled_q |= ~Q(**{f"{field}__isnull": True})

    # Unknown flags must be FALSE
    unknown_true_q = (
        Q(tx_unknown_month=True) |
        Q(tx_unknown_year=True) |
        Q(ltf_months_unknown=True) |
        Q(regimen_months_unknown=True)
    )

    # Final issue condition
    missing_tx_previous_2_3_tb_filled_qs = qs.filter(
        tx_previous_2_3_q
    ).filter(
        tb_fields_filled_q | unknown_true_q
    )
    
    missing_tx_previous_2_3_tb_filled = missing_tx_previous_2_3_tb_filled_qs.count()
    
    counts = {
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
        "missing_tx_previous_2_3_tb_filled" : missing_tx_previous_2_3_tb_filled
    }

    # Count issues
    counts["total_issues"] = sum(counts.values())

    return counts
