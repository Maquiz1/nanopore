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

    xpert_in_2_6_q = Q(xpert_mtb__value__in=[2,3,4,5,6]) | Q(xpert_mtb__name__in=["2","3","4","5","6"])
    xpert_is_8_q = Q(xpert_mtb__value=8) | Q(xpert_mtb__name__iexact="8")

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

    # AFB
    missing_afb_microscopy_conducted = qs.filter(
        afb_xpert_required_q,
        afb_microscopy_conducted__isnull=True
    )

    missing_afb_a_date = qs.filter(afb_yes_q, afb_a_date__isnull=True)
    missing_technique_a = qs.filter(afb_yes_q, technique_a__isnull=True)
    missing_afb_a_results = qs.filter(afb_yes_q, afb_a_results__isnull=True)

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
        "missing_date_sample1_collected": missing_date_sample1_collected,
        "missing_date_sample1_received": missing_date_sample1_received,
        "missing_appearance_sample1": missing_appearance_sample1,
        "missing_sample1_volume": missing_sample1_volume,
        "missing_invalid_sample1_volume": invalid_sample1_volume,
        "missing_date_sample2_collected": missing_date_sample2_collected,
        "missing_date_sample2_received": missing_date_sample2_received,
        "missing_appearance_sample2": missing_appearance_sample2,
        "missing_sample2_volume": missing_sample2_volume,
        "missing_invalid_sample2_volume": invalid_sample2_volume,
        "missing_afb_microscopy_conducted": missing_afb_microscopy_conducted,
        "missing_afb_a_date": missing_afb_a_date,
        "missing_technique_a": missing_technique_a,
        "missing_afb_a_results": missing_afb_a_results,
        "missing_xpert_mtb_rif_conducted": missing_xpert_mtb_rif_conducted,
        "missing_xpert_date": missing_xpert_date,
        "missing_xpert_mtb": missing_xpert_mtb,
        "missing_error_code": missing_error_code,
        "missing_xpert_rif": missing_xpert_rif,
        "missing_ct_value": missing_ct_value,
    }

    totals = {f"count_{k}": v.count() for k, v in problem_lists.items()}
    totals["clinic_report_total"] = sum(totals.values())

    return problem_lists, totals
