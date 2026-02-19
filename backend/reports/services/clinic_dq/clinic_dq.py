# reports/services/clinic_dq.py

from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role


def get_clinic_queryset(user, zone_id=None, site_id=None):
    Clinic = apps.get_model("nanopore", "ClinicLaboratory")

    qs = Clinic.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district",
        "screening__site__district__region",
        "screening__site__district__region__zone",
        "sample_received",
        "number_received",
        "new_sample",
        "sample_reason",
        "appearance_sample1",
        "appearance_sample2",
        "afb_microscopy_conducted",
        "xpert_mtb_rif_conducted",
        "xpert_mtb",
    )

    qs = filter_queryset_by_user_role(user, qs, site_field="screening__site")

    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)

    if site_id:
        qs = qs.filter(screening__site_id=site_id)

    return qs


def get_clinic_dq(qs):
    def is_true(field):
        """
        Field is explicitly True
        """
        return Q(**{field: True})


    def is_false(field):
        """
        Field is explicitly False
        """
        return Q(**{field: False})


    def is_checked(field):
        """
        Checkbox is checked (True)
        """
        return Q(**{field: True})


    def is_unchecked(field):
        """
        Checkbox is False OR NULL (treat as not checked)
        Useful when BooleanField(null=True)
        """
        return Q(**{field: False}) | Q(**{f"{field}__isnull": True})

    
    def is_filled_char(field):
        return (
            Q(**{f"{field}__isnull": False}) &
            ~Q(**{f"{field}__regex": r'^\s*$'})
        )

    def is_filled_non_char(field):
        return Q(**{f"{field}__isnull": False})
    
    def m2m_has_any(field):
        return Q(**{f"{field}__isnull": False})

    # ─────────────────────────────────────────────
    # Q Helpers
    # ─────────────────────────────────────────────

    sample_received_is_2_q = Q(sample_received__value=2) | Q(sample_received__name__iexact="2")
    sample_received_is_1_q = Q(sample_received__value=1) | Q(sample_received__name__iexact="1")
    new_sample_is_1_q = Q(new_sample__value=1) | Q(new_sample__name__iexact="1")
    new_sample_is_2_q = Q(new_sample__value=2) | Q(new_sample__name__iexact="2")
    sample_reason_is_96_q = Q(sample_reason__value=96) | Q(sample_reason__name__iexact="96")

    number_required_q = sample_received_is_1_q | sample_received_is_2_q | new_sample_is_1_q
    afb_xpert_required_q = sample_received_is_1_q | (sample_received_is_2_q & new_sample_is_1_q)

    afb_yes_q = Q(afb_microscopy_conducted__name__iexact="yes")
    xpert_yes_q = Q(xpert_mtb_rif_conducted__name__iexact="yes")

    # EXPERT MTB
    xpert_in_2_6_q = Q(xpert_mtb__value__in=[2,3,4,5,6]) | Q(xpert_mtb__name__in=["2","3","4","5","6"])
    xpert_is_8_q = Q(xpert_mtb__value=8) | Q(xpert_mtb__name__iexact="8")
    
    # xpert_mtb_rif_conducted = 2 → fields (xpert_date,xpert_mtb) must be EMPTY
    xpert_mtb_rif_conducted_2_q = (
        Q(xpert_mtb_rif_conducted=2) |
        Q(xpert_mtb_rif_conducted__value=2) |
        Q(xpert_mtb_rif_conducted__name__iexact="2")
    )
    
    invalid_xpert_mtb_rif_conducted_2_filled = qs.filter(
        xpert_mtb_rif_conducted_2_q &
        (
            Q(xpert_date__isnull=False) |
            Q(xpert_mtb__isnull=False)
        )
    )

    # xpert_mtb = 1,7,8,9 → fields (tb_regimen_other) must be EMPTY
    xpert_mtb_condition_q = (
        Q(xpert_mtb__in=[1,7,8,9]) |
        Q(xpert_mtb__value__in=[1,7,8,9]) |
        Q(xpert_mtb__name__in=["1","7","8","9"])
    )
    
    case_invalid_xpert_mtb_q = (
        is_filled_non_char("error_code") |
        is_filled_non_char("xpert_rif") |
        is_filled_non_char("ct_value") |
        is_true("ct_na")
    )

    invalid_xpert_mtb_filled = qs.filter(
        xpert_mtb_condition_q & case_invalid_xpert_mtb_q
    )

    # ─────────────────────────────────────────────
    # Volume Validation
    # ─────────────────────────────────────────────

    invalid_sample1_volume = qs.filter(
        sample1_volume__isnull=False
    ).exclude(
        sample1_volume__regex=r'^[0-9]+(\.[0-9]+)?$'
    )

    invalid_sample2_volume = qs.filter(
        sample2_volume__isnull=False
    ).exclude(
        sample2_volume__regex=r'^[0-9]+(\.[0-9]+)?$'
    )

    # ─────────────────────────────────────────────
    # Missing Fields
    # ─────────────────────────────────────────────

    missing_sample_received = qs.filter(sample_received__isnull=True)

    missing_number_received = qs.filter(
        number_required_q,
        number_received__isnull=True
    )

    missing_sample_reason_when_received_2 = qs.filter(
        sample_received_is_2_q,
        sample_reason__isnull=True
    )

    missing_new_reason_when_new_sample_2 = qs.filter(
        new_sample_is_2_q,
        new_reason__isnull=True
    )

    missing_other_reason_when_sample_reason_96 = qs.filter(
        sample_reason_is_96_q,
        other_reason__isnull=True
    )
    
    # SAMPLE RECEIVED RULE
    # ────────────────
    # SAMPLE / NEW SAMPLE RULES
    # ────────────────

    # 1️⃣ Case 1 — sample_received = 1 → sample_reason AND new_sample must be empty
    sample_received_1_q = (
        Q(sample_received=1) |
        Q(sample_received__value=1) |
        Q(sample_received__name__iexact="1")
    )

    invalid_sample_received_1 = qs.filter(
        sample_received_1_q & (
            is_filled_non_char("sample_reason") |  # must be empty
            is_filled_non_char("new_sample")      # must be empty
        )
    )

    # 2️⃣ Case 2 — sample_received = 2 AND new_sample = 2 → number_received must be empty
    sample_received_2_q = (
        Q(sample_received=2) |
        Q(sample_received__value=2) |
        Q(sample_received__name__iexact="2")
    )

    new_sample_2_q = (
        Q(new_sample=2) |
        Q(new_sample__value=2) |
        Q(new_sample__name__iexact="2")
    )

    invalid_sample_received_2_new_sample_2 = qs.filter(
        sample_received_2_q & new_sample_2_q & is_filled_non_char("number_received")
    )

    # Combine both rules
    invalid_sample_sample_received_rule = invalid_sample_received_1 | invalid_sample_received_2_new_sample_2

    # SAMPLE REASON RULE
    # Sample reason = 1 → other_reason must be empty
    # Sample reason = 1 or 2 → other_reason must be empty
    sample_reason_1_2_q = (
        Q(sample_reason__in=[1, 2]) |
        Q(sample_reason__value__in=[1, 2]) |
        Q(sample_reason__name__in=["1", "2"])
    )

    invalid_other_reason_rule = qs.filter(
        sample_reason_1_2_q & is_filled_char("other_reason")
    )


    # Sample 1
    missing_date_sample1_collected = qs.filter(
        number_received__isnull=False,
        date_sample1_collected__isnull=True
    )

    missing_date_sample1_received = qs.filter(
        number_received__isnull=False,
        date_sample1_received__isnull=True
    )

    missing_appearance_sample1 = qs.filter(
        number_received__isnull=False,
        appearance_sample1__isnull=True
    )

    missing_sample1_volume = qs.filter(
        number_received__isnull=False,
        sample1_volume__isnull=True
    )

    # Sample 2
    missing_date_sample2_collected = qs.filter(
        number_received__value=2,
        date_sample2_collected__isnull=True
    )

    missing_date_sample2_received = qs.filter(
        number_received__value=2,
        date_sample2_received__isnull=True
    )

    missing_appearance_sample2 = qs.filter(
        number_received__value=2,
        appearance_sample2__isnull=True
    )

    missing_sample2_volume = qs.filter(
        number_received__value=2,
        sample2_volume__isnull=True
    )

    # Invalid Sample
    number_received_1_q = Q(number_received=1) | Q(number_received__value=1) | Q(number_received__name__iexact="1")

    invalid_number_received_1_filled = qs.filter(
        number_received_1_q &
        (
            is_filled_non_char("date_sample2_collected") |
            is_filled_non_char("date_sample2_received") |
            is_filled_non_char("appearance_sample2") |
            is_filled_non_char("sample2_volume")
        )
    )
    
    
    # AFB
    missing_afb_microscopy_conducted = qs.filter(
        afb_xpert_required_q,
        afb_microscopy_conducted__isnull=True
    )

    missing_afb_a_date = qs.filter(afb_yes_q, afb_a_date__isnull=True)
    missing_technique_a = qs.filter(afb_yes_q, technique_a__isnull=True)
    missing_afb_a_results = qs.filter(afb_yes_q, afb_a_results__isnull=True)
    
    # AFB B (must match clinic_dq_counts.py logic)
    missing_afb_b_base_q = (
        afb_yes_q &
        Q(
            afb_a_date__isnull=False,
            technique_a__isnull=False,
            afb_a_results__isnull=False
        ) &
        (
            Q(afb_b_date__isnull=True) |
            Q(technique_b__isnull=True) |
            Q(afb_b_results__isnull=True)
        )
    )

    missing_afb_b_date = qs.filter(
        missing_afb_b_base_q,
        afb_b_date__isnull=True
    )

    missing_technique_b = qs.filter(
        missing_afb_b_base_q,
        technique_b__isnull=True
    )

    missing_afb_b_results = qs.filter(
        missing_afb_b_base_q,
        afb_b_results__isnull=True
    )
    
    
    afb_microscopy_conducted_condition_2_q = (
        Q(afb_microscopy_conducted=2) |
        Q(afb_microscopy_conducted__value=2) |
        Q(afb_microscopy_conducted__name__iexact="2")
    )
    
    invalid_afb_microscopy_conducted_filled = qs.filter(
        afb_microscopy_conducted_condition_2_q &
        (
            is_filled_non_char("afb_a_date") |
            is_filled_non_char("afb_b_date") |
            is_filled_non_char("technique_a") |
            is_filled_non_char("technique_b") |
            is_filled_non_char("afb_a_results") |
            is_filled_non_char("afb_b_results")
        )
    )

    # Xpert
    missing_xpert_mtb_rif_conducted = qs.filter(
        afb_xpert_required_q,
        xpert_mtb_rif_conducted__isnull=True
    )

    missing_xpert_date = qs.filter(xpert_yes_q, xpert_date__isnull=True)
    missing_xpert_mtb = qs.filter(xpert_yes_q, xpert_mtb__isnull=True)
    missing_error_code = qs.filter(xpert_is_8_q, error_code__isnull=True)
    missing_xpert_rif = qs.filter(xpert_in_2_6_q, xpert_rif__isnull=True)

    missing_ct_value = qs.filter(
        xpert_in_2_6_q
    ).exclude(
        Q(ct_value__isnull=False, ct_na=False) |
        Q(ct_value__isnull=True, ct_na=True) |
        Q(ct_value__in=[99, 99.0])
    )

    # ─────────────────────────────────────────────
    # Collect Querysets
    # ─────────────────────────────────────────────

    problem_lists = {
        "missing_sample_received": missing_sample_received,
        "missing_number_received": missing_number_received,
        "missing_sample_reason_when_received_2": missing_sample_reason_when_received_2,
        "missing_new_reason_when_new_sample_2": missing_new_reason_when_new_sample_2,
        "missing_other_reason_when_sample_reason_96": missing_other_reason_when_sample_reason_96,
        
        "invalid_sample_sample_received_rule":invalid_sample_sample_received_rule,
        "invalid_other_reason_rule":invalid_other_reason_rule,
        # "invalid_new_sample_rule":invalid_new_sample_rule,

        # Sample 1
        "missing_date_sample1_collected": missing_date_sample1_collected,
        "missing_date_sample1_received": missing_date_sample1_received,
        "missing_appearance_sample1": missing_appearance_sample1,
        "missing_sample1_volume": missing_sample1_volume,
        
        # INVALID SAMPLE 1 VOLUME
        "missing_invalid_sample1_volume": invalid_sample1_volume,
        
        # INVALID RULE FOR ALL
        "invalid_number_received_1_filled":invalid_number_received_1_filled,
        
        # Sample 2
        "missing_date_sample2_collected": missing_date_sample2_collected,
        "missing_date_sample2_received": missing_date_sample2_received,
        "missing_appearance_sample2": missing_appearance_sample2,
        "missing_sample2_volume": missing_sample2_volume,
        
        # INVALID SAMPLE 2 VOLUME
        "missing_invalid_sample2_volume": invalid_sample2_volume,

        # AFB
        "missing_afb_microscopy_conducted": missing_afb_microscopy_conducted,
        "missing_afb_a_date": missing_afb_a_date,
        "missing_technique_a": missing_technique_a,
        "missing_afb_a_results": missing_afb_a_results,

        "missing_afb_b_date": missing_afb_b_date,
        "missing_technique_b": missing_technique_b,
        "missing_afb_b_results": missing_afb_b_results,
        "invalid_afb_microscopy_conducted_filled":invalid_afb_microscopy_conducted_filled,
        
        # expert mtb
        "missing_xpert_mtb_rif_conducted": missing_xpert_mtb_rif_conducted,
        "missing_xpert_date": missing_xpert_date,
        "missing_xpert_mtb": missing_xpert_mtb,
        "invalid_xpert_mtb_rif_conducted_2_filled":invalid_xpert_mtb_rif_conducted_2_filled,
        "missing_error_code": missing_error_code,
        "missing_xpert_rif": missing_xpert_rif,
        "missing_ct_value": missing_ct_value,
        "invalid_xpert_mtb_filled":invalid_xpert_mtb_filled,
    }

    totals = {f"count_{k}": v.count() for k, v in problem_lists.items()}
    totals["clinic_report_total"] = sum(totals.values())

    return problem_lists, totals
