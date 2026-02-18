# reports/services/enrollment_dq.py

from django.apps import apps
from django.db.models import Count, Q
from utils.permissions import filter_queryset_by_user_role
from django.db.models.functions import Trim


def get_enrollment_queryset(user, zone_id=None, site_id=None):
    Enrollment = apps.get_model("nanopore", "Enrollment")

    qs = Enrollment.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district",
        "screening__site__district__region",
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

    return qs


def get_enrollment_dq(qs):

    # ─────────────────────────────────────────────
    # BASIC REQUIRED FIELDS
    # ─────────────────────────────────────────────

    missing_tx_previous = qs.filter(tx_previous__isnull=True)

    missing_hiv_status = qs.filter(hiv_status__isnull=True)

    missing_other_diseases = qs.filter(other_diseases__isnull=True)

    #  Samples collections

    missing_sputum_collected = qs.filter(sputum_collected__isnull=True)

    missing_sputum_date = qs.filter(
        sputum_collected=1,
        sputum_date__isnull=True
    )

    missing_sputum_reasons = qs.filter(
        sputum_collected=2,
        sputum_reasons__isnull=True
    )

    # INVALID SPUTUMS
    # -------------------------------
    # sputum_reasons check: sputum_collected=1 → sputum_reasons must be empty
    # -------------------------------
    invalid_sputum_reasons_qs = qs.annotate(
        sputum_reasons_trimmed=Trim("sputum_reasons")
    ).filter(
        Q(sputum_collected=1) &
        Q(sputum_reasons_trimmed__isnull=False) &
        ~Q(sputum_reasons_trimmed="")
    )


    # -------------------------------
    # sputum_date check: sputum_collected=2 → sputum_date must be empty
    # -------------------------------
    invalid_sputum_date_qs = qs.filter(
        Q(sputum_collected=2) & ~Q(sputum_date__isnull=True)
    )
    
    # DISEASE MEDICAL
    missing_diseases_medical = (
        qs.filter(other_diseases=1)
        .annotate(diseases_medical_count=Count("diseases_medical", distinct=True))
        .filter(diseases_medical_count=0)
    )

    missing_diseases_specify = qs.filter(
        diseases_medical__value=96
    ).filter(
        Q(diseases_specify__isnull=True) | Q(diseases_specify="")
    ).distinct()
    
    invalid_diseases_medical_qs = qs.filter(
        Q(other_diseases__in=[2, 3]) &
        Q(diseases_medical__isnull=False)
    ).distinct()
    
    invalid_diseases_specify_qs = qs.annotate(
        diseases_specify_trimmed=Trim("diseases_specify")
    ).filter(
        # diseases_specify is filled (not null, not empty, not whitespace)
        Q(diseases_specify_trimmed__isnull=False) &
        ~Q(diseases_specify_trimmed="") &
        # AND condition is NOT the allowed one
        ~(
            Q(other_diseases=11) &
            Q(other_diseases__value=96)
        )
    )

    # ─────────────────────────────────────────────
    # TB Treatment (tx_previous = 1)
    # ─────────────────────────────────────────────

    previous_tx = qs.filter(tx_previous=1)
    
    # TB CATEGORY
    missing_tb_category = qs.filter(
        tx_previous=1
    ).filter(
        Q(tb_category__isnull=True)
    )
    
    missing_tb_category_specify = qs.filter(
        tb_category__value=96
    ).filter(
        Q(tb_category_specify__isnull=True) | Q(tb_category_specify="")
    )
    
    # TB CATEGORY SPECIFY NOT REQUIRED
    # Categories where "specify" should be empty
    tb_category_1_2_3_5_q = Q(tb_category__in=[1, 2, 3, 5])

    # Fields that should be empty for these categories
    tb_category_specify_char_fields = ["tb_category_specify"]

    # Build a Q object for fields that are NOT empty
    tb_category_specify_filled = Q()
    for field in tb_category_specify_char_fields:
        tb_category_specify_filled |= (
            ~Q(**{f"{field}__isnull": True}) &
            ~Q(**{f"{field}": ""})
        )

    # Filter invalid rows: category in [1,2,3,5] AND "specify" is filled
    invalid_tb_category_1_2_3_5 = qs.filter(
        tb_category_1_2_3_5_q & tb_category_specify_filled
    )
    
    # TB 10e. If LTF or treatment failure for how long the participant received TB treatment? ( Months): NOT REQUIRED
    # Categories where LTF fields should be empty / False
    tb_category_1_4_5_q = Q(tb_category__in=[1, 4, 5])

    # Non-char fields to check for emptiness
    ltf_months_non_char_fields = ["ltf_months"]

    # Q for fields that are filled (i.e., invalid)
    ltf_months_filled = Q()
    for field in ltf_months_non_char_fields:
        ltf_months_filled |= ~Q(**{f"{field}__isnull": True})

    # Also check if unknown flag is True
    ltf_months_invalid_flag = Q(ltf_months_unknown=True)

    # Combine conditions: either filled or unknown=True
    invalid_ltf_months_q = ltf_months_filled | ltf_months_invalid_flag

    # Final filter: category in [1,4,5] AND invalid LTF fields
    invalid_tb_category_1_4_5 = qs.filter(
        tb_category_1_4_5_q & invalid_ltf_months_q
    )
    
    # DR OR DS
    missing_dr_ds = previous_tx.filter(dr_ds__isnull=True)

    missing_tb_regimen = previous_tx.filter(tb_regimen__isnull=True)

    missing_tb_outcome = previous_tx.filter(tb_otcome__isnull=True)

    missing_tb_regimen_specify = qs.filter(
        tb_regimen__value=96
    ).filter(
        Q(tb_regimen_specify__isnull=True) | Q(tb_regimen_specify="")
    )

    missing_tb_regimen_specify_8 = qs.filter(
        tb_regimen=8
    ).filter(
        Q(tb_regimen_specify__isnull=True) | Q(tb_regimen_specify="")
    )

    invalid_ltf_months = qs.filter(
        tb_category__in=[2, 3]
    ).exclude(
        Q(ltf_months__isnull=False, ltf_months_unknown=False) |
        Q(ltf_months__isnull=True, ltf_months_unknown=True)
    )

    # ─────────────────────────────────────────────
    # Previous TB Month/Year Validations
    # ─────────────────────────────────────────────

    missing_tx_month_without_unknown = previous_tx.filter(
        tx_month__isnull=True,
        tx_unknown_month=False
    )

    invalid_tx_month_with_unknown = previous_tx.filter(
        tx_unknown_month=True
    ).exclude(
        Q(tx_month__isnull=True) | Q(tx_month=99)
    )

    missing_tx_year_without_unknown = previous_tx.filter(
        tx_year__isnull=True,
        tx_unknown_year=False
    )

    invalid_tx_year_with_unknown = previous_tx.filter(
        tx_unknown_year=True
    ).exclude(
        Q(tx_year__isnull=True) | Q(tx_year=99)
    )

    invalid_unknown_year_dependencies = previous_tx.filter(
        tx_unknown_year=True
    ).exclude(
        Q(tx_month__isnull=True) | Q(tx_month=99),
        tx_unknown_month=True
    )

    missing_regimen_months_without_unknown = previous_tx.filter(
        regimen_months__isnull=True,
        regimen_months_unknown=False
    )

    invalid_regimen_months_with_unknown = previous_tx.filter(
        regimen_months_unknown=True
    ).exclude(
        regimen_months__isnull=True
    )

    # ─────────────────────────────────────────────
    # tx_previous = 2 or 3 → TB fields must be empty
    # ─────────────────────────────────────────────

    tx_previous_2_3_q = Q(tx_previous__in=[2, 3])

    char_fields = [
        "tb_category_specify",
        "tb_regimen_specify",
    ]

    non_char_fields = [
        "tb_category",
        "tx_month",
        "tx_year",
        "dr_ds",
        "ltf_months",
        "tb_regimen",
        "regimen_months",
        "tb_otcome",
    ]

    tb_fields_filled_q = Q()

    for field in char_fields:
        tb_fields_filled_q |= (
            ~Q(**{f"{field}__isnull": True}) &
            ~Q(**{f"{field}": ""})
        )

    for field in non_char_fields:
        tb_fields_filled_q |= ~Q(**{f"{field}__isnull": True})

    unknown_true_q = (
        Q(tx_unknown_month=True) |
        Q(tx_unknown_year=True) |
        Q(ltf_months_unknown=True) |
        Q(regimen_months_unknown=True)
    )

    missing_tx_previous_2_3_tb_filled = qs.filter(
        tx_previous_2_3_q
    ).filter(
        tb_fields_filled_q | unknown_true_q
    )

    # ─────────────────────────────────────────────
    # Collect Querysets
    # ─────────────────────────────────────────────

    counts = {
        "missing_tx_previous":missing_tx_previous,
        "missing_tb_category":missing_tb_category,
        "invalid_tb_category_1_2_3_5":invalid_tb_category_1_2_3_5,
        "invalid_tb_category_1_4_5":invalid_tb_category_1_4_5,
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
        "missing_tx_previous_2_3_tb_filled": missing_tx_previous_2_3_tb_filled,
        "missing_hiv_status": missing_hiv_status,
        "missing_other_diseases": missing_other_diseases,
        "missing_diseases_medical": missing_diseases_medical,
        "missing_diseases_specify": missing_diseases_specify,
        "invalid_diseases_medical_qs":invalid_diseases_medical_qs,
        "invalid_diseases_specify_qs":invalid_diseases_specify_qs,
        "missing_sputum_collected": missing_sputum_collected,
        "invalid_sputum_reasons_qs":invalid_sputum_reasons_qs,
        "invalid_sputum_date_qs":invalid_sputum_date_qs,
        "missing_sputum_date": missing_sputum_date,
        "missing_sputum_reasons": missing_sputum_reasons,
    }

    totals = {f"count_{k}": v.count() for k, v in counts.items()}
    totals["enrollment_report_total"] = sum(totals.values())

    return counts, totals
