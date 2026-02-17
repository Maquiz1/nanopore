# reports/context_processors/clinic_context.py

from reports.services.clinic_dq import (
    get_clinic_queryset,
    get_clinic_dq,
)


def clinic_report_total(request):
    """
    Navbar clinic data quality counter.
    Uses clinic_dq service to avoid duplicated logic.
    """

    if not request.user.is_authenticated:
        return {
            "context_clinic_report_total": 0
        }

    # No zone/site filters for navbar (global view based on role)
    qs = get_clinic_queryset(request.user)

    problem_lists, stats = get_clinic_dq(qs)

    total_issues = stats.get("clinic_report_total", 0)

    return {
        "context_clinic_report_total": total_issues,
        **stats,   # gives count_missing_...
    }


# from django.apps import apps
# from django.db.models import Q
# from utils.permissions import filter_queryset_by_user_role
# from utils.roles import get_role_context

# def clinic_report_total(request):
#     """
#     Returns clinic data quality issue counts for navbar with conditional logic
#     aligned to ClinicDataQualityReportView:
#     - sample / number / reason rules
#     - sample1/sample2 presence rules
#     - AFB conditional fields when afb_microscopy_conducted == Yes
#     - Xpert conditional fields when xpert_mtb_rif_conducted == Yes
#     - Xpert-dependent rules for error_code, xpert_rif, and CT validity

#     NOTE: afb_microscopy_conducted and xpert_mtb_rif_conducted are required when:
#       - sample_received == 1
#       OR
#       - sample_received == 2 AND new_sample == 1
#     """
#     if not request.user.is_authenticated:
#         return {
#             "clinic_report_total": 0,
#             # base fields
#             "missing_sample_received": 0,
#             "missing_number_received": 0,
#             "missing_afb_microscopy_conducted": 0,
#             "missing_xpert_mtb_rif_conducted": 0,
#             # sample1/sample2 fields
#             "missing_date_sample1_collected": 0,
#             "missing_date_sample1_received": 0,
#             "missing_appearance_sample1": 0,
#             "missing_sample1_volume": 0,
#             "missing_date_sample2_collected": 0,
#             "missing_date_sample2_received": 0,
#             "missing_appearance_sample2": 0,
#             "missing_sample2_volume": 0,
#             # sample/new reason rules
#             "missing_sample_reason_when_received_2": 0,
#             "missing_new_reason_when_new_sample_2": 0,
#             "missing_other_reason_when_sample_reason_96": 0,
#             # AFB conditional fields
#             "missing_afb_a_date": 0,
#             "missing_technique_a": 0,
#             "missing_afb_a_results": 0,
#             "missing_afb_b_date": 0,
#             "missing_technique_b": 0,
#             "missing_afb_b_results": 0,
#             # Xpert conditional fields
#             "missing_xpert_date": 0,
#             "missing_xpert_mtb": 0,
#             "missing_error_code": 0,
#             "missing_xpert_rif": 0,
#             "missing_ct_value": 0,
#         }
        
        
#     role_context = get_role_context(request.user)
#     is_zonal_lab = role_context.get("is_zonal_lab", False)
#     is_admin     = role_context.get("is_admin", False)
#     is_reviewer  = role_context.get("is_reviewer", False)
#     is_superuser = request.user.is_superuser
#     is_full_access = is_admin or is_superuser
#     is_privileged = is_admin or is_reviewer

#     Clinic = apps.get_model('nanopore', 'ClinicLaboratory')
#     clinics = Clinic.objects.all()
#     clinics = filter_queryset_by_user_role(request.user, clinics, site_field="screening__site")

#     # --- Q helpers (match those used in the view) ---
#     sample_received_is_1_q = Q(sample_received__value=1) | Q(sample_received__name__iexact="1")
#     sample_received_is_2_q = Q(sample_received__value=2) | Q(sample_received__name__iexact="2")
#     new_sample_is_1_q = Q(new_sample__value=1) | Q(new_sample__name__iexact="1")
#     new_sample_is_2_q = Q(new_sample__value=2) | Q(new_sample__name__iexact="2")
#     sample_reason_is_96_q = Q(sample_reason__value=96) | Q(sample_reason__name__iexact="96")

#     nr_is_2_q = Q(number_received__value=2) | Q(number_received__name__iexact="2")
#     nr_present_q = Q(number_received__isnull=False)

#     afb_yes_q = Q(afb_microscopy_conducted__name__iexact="yes")
#     xpert_yes_q = Q(xpert_mtb_rif_conducted__name__iexact="yes")

#     xpert_in_2_6_q = Q(xpert_mtb__value__in=[2, 3, 4, 5, 6]) | Q(xpert_mtb__name__in=["2", "3", "4", "5", "6"])
#     xpert_is_8_q = Q(xpert_mtb__value=8) | Q(xpert_mtb__name__iexact="8")

#     # --- New requirement: afb/xpert required when sample_received == 1 OR (sample_received == 2 AND new_sample == 1) ---
#     afb_xpert_required_q = sample_received_is_1_q | (sample_received_is_2_q & new_sample_is_1_q)

#     # --- Base counts ---
#     missing_sample_received = clinics.filter(sample_received__isnull=True).count()

#     # number_received required when sample_received in (1,2) OR new_sample == 1
#     number_required_q = (sample_received_is_1_q | sample_received_is_2_q | new_sample_is_1_q)
#     missing_number_received = clinics.filter(number_required_q, number_received__isnull=True).count()

#     # When number_received is required, also require afb_microscopy_conducted and xpert_mtb_rif_conducted
#     # Keep the original "number_required" checks for backward compatibility, but enforce the stricter rule
#     # (afb_xpert_required_q) as the primary requirement per request.
#     missing_afb_microscopy_conducted = clinics.filter(afb_xpert_required_q, afb_microscopy_conducted__isnull=True).count()
#     missing_xpert_mtb_rif_conducted = clinics.filter(afb_xpert_required_q, xpert_mtb_rif_conducted__isnull=True).count()

#     # sample_reason required when sample_received == 2
#     missing_sample_reason_when_received_2 = clinics.filter(sample_received_is_2_q, sample_reason__isnull=True).count()

#     # new_reason required when new_sample == 2
#     missing_new_reason_when_new_sample_2 = clinics.filter(new_sample_is_2_q, new_reason__isnull=True).count()

#     # other_reason required when sample_reason == 96
#     missing_other_reason_when_sample_reason_96 = clinics.filter(sample_reason_is_96_q, other_reason__isnull=True).count()

#     # sample1 required when number_received provided
#     missing_date_sample1_collected = clinics.filter(nr_present_q, date_sample1_collected__isnull=True).count()
#     missing_date_sample1_received = clinics.filter(nr_present_q, date_sample1_received__isnull=True).count()
#     missing_appearance_sample1 = clinics.filter(nr_present_q, appearance_sample1__isnull=True).count()
#     missing_sample1_volume = clinics.filter(nr_present_q, sample1_volume__isnull=True).count()
#     invalid_sample1_volume = clinics.filter(
#             sample1_volume__isnull=False
#         ).exclude(
#             sample1_volume__regex=r'^[0-9]+(\.[0-9]+)?$'
#         )
        
#     # sample2 required only when number_received == 2
#     missing_date_sample2_collected = clinics.filter(nr_is_2_q, date_sample2_collected__isnull=True).count()
#     missing_date_sample2_received = clinics.filter(nr_is_2_q, date_sample2_received__isnull=True).count()
#     missing_appearance_sample2 = clinics.filter(nr_is_2_q, appearance_sample2__isnull=True).count()
#     missing_sample2_volume = clinics.filter(nr_is_2_q, sample2_volume__isnull=True).count()   
#     invalid_sample2_volume = clinics.filter(
#             sample2_volume__isnull=False
#         ).exclude(
#             sample2_volume__regex=r'^[0-9]+(\.[0-9]+)?$'
#         )
        
#     # AFB conditional when afb_microscopy_conducted == Yes
#     missing_afb_a_date = clinics.filter(afb_yes_q, afb_a_date__isnull=True).count()
#     missing_technique_a = clinics.filter(afb_yes_q, technique_a__isnull=True).count()
#     missing_afb_a_results = clinics.filter(afb_yes_q, afb_a_results__isnull=True).count()
    
#     # # -----------------------------------------------------
#     # # define “any B data entered”
#     # # -----------------------------------------------------
#     # # AFB B depends on AFB A being complete
#     # # -----------------------------------------------------

#     # # Step 1: define partial B
#     # afb_b_partial_q = (
#     #     (
#     #         Q(afb_b_date__isnull=False) |
#     #         Q(technique_b__isnull=False) |
#     #         Q(afb_b_results__isnull=False)
#     #     )
#     #     &
#     #     (
#     #         Q(afb_b_date__isnull=True) |
#     #         Q(technique_b__isnull=True) |
#     #         Q(afb_b_results__isnull=True)
#     #     )
#     # )
    
#     # # Step 2: count missing fields only inside partial B
#     # missing_afb_b_date = clinics.filter(
#     #     afb_yes_q &
#     #     afb_b_partial_q &
#     #     Q(afb_b_date__isnull=True)
#     # ).count()

#     # missing_technique_b = clinics.filter(
#     #     afb_yes_q &
#     #     afb_b_partial_q &
#     #     Q(technique_b__isnull=True)
#     # ).count()

#     # missing_afb_b_results = clinics.filter(
#     #     afb_yes_q &
#     #     afb_b_partial_q &
#     #     Q(afb_b_results__isnull=True)
#     # ).count()
    
    
#     afb_a_complete_q = (
#         Q(afb_a_date__isnull=False) &
#         Q(technique_a__isnull=False) &
#         Q(afb_a_results__isnull=False)
#     )
#     # -----------------------------------------------------
#     # AFB B depends on AFB A being complete
#     # -----------------------------------------------------

#     # any B data entered
#     afb_b_started_q = (
#         Q(afb_b_date__isnull=False) |
#         Q(technique_b__isnull=False) |
#         Q(afb_b_results__isnull=False)
#     )

#     # partial B = some entered but not all
#     afb_b_partial_q = (
#         afb_b_started_q &
#         (
#             Q(afb_b_date__isnull=True) |
#             Q(technique_b__isnull=True) |
#             Q(afb_b_results__isnull=True)
#         )
#     )

#     missing_afb_b_date = clinics.filter(
#         afb_yes_q &
#         afb_a_complete_q &      # ✅ REQUIRED
#         afb_b_partial_q &
#         Q(afb_b_date__isnull=True)
#     ).count()

#     missing_technique_b = clinics.filter(
#         afb_yes_q &
#         afb_a_complete_q &      # ✅ REQUIRED
#         afb_b_partial_q &
#         Q(technique_b__isnull=True)
#     ).count()

#     missing_afb_b_results = clinics.filter(
#         afb_yes_q &
#         afb_a_complete_q &      # ✅ REQUIRED
#         afb_b_partial_q &
#         Q(afb_b_results__isnull=True)
#     ).count()

#     # Xpert conditional when xpert_mtb_rif_conducted == Yes
#     missing_xpert_date = clinics.filter(xpert_yes_q, xpert_date__isnull=True).count()
#     missing_xpert_mtb = clinics.filter(xpert_yes_q, xpert_mtb__isnull=True).count()

#     # xpert_mtb dependent checks
#     missing_error_code = clinics.filter(xpert_is_8_q, error_code__isnull=True).count()
#     missing_xpert_rif = clinics.filter(xpert_in_2_6_q, xpert_rif__isnull=True).count()

#     # CT validity: valid if (ct_value present AND ct_na is False) OR (ct_value missing AND ct_na is True) OR ct_value = 99 OR 99.0, regardless of ct_na (ct_value in [99, 99.0])
#     valid_ct_q = Q(ct_value__isnull=False, ct_na=False) | Q(ct_value__isnull=True, ct_na=True) | Q(ct_value__in=[99, 99.0])

#     missing_ct_value = clinics.filter(xpert_in_2_6_q).exclude(valid_ct_q).count()

#     # --- Aggregate total issues (sum of all counts above) ---
#     clinic_report_total = (
#         missing_sample_received
#         + missing_number_received
#         + missing_afb_microscopy_conducted
#         + missing_xpert_mtb_rif_conducted
#         + missing_sample_reason_when_received_2
#         + missing_new_reason_when_new_sample_2
#         + missing_other_reason_when_sample_reason_96
#         + missing_date_sample1_collected
#         + missing_date_sample1_received
#         + missing_appearance_sample1
#         + missing_sample1_volume
#         + invalid_sample1_volume.count()
#         + missing_date_sample2_collected
#         + missing_date_sample2_received
#         + missing_appearance_sample2
#         + missing_sample2_volume
#         + invalid_sample2_volume.count()
#         + missing_afb_a_date
#         + missing_technique_a
#         + missing_afb_a_results
#         + missing_afb_b_date
#         + missing_technique_b
#         + missing_afb_b_results
#         + missing_xpert_date
#         + missing_xpert_mtb
#         + missing_error_code
#         + missing_xpert_rif
#         + missing_ct_value
#     )

#     return {
#         "context_clinic_report_total": clinic_report_total,
#         "missing_sample_received": missing_sample_received,
#         "missing_number_received": missing_number_received,
#         "missing_afb_microscopy_conducted": missing_afb_microscopy_conducted,
#         "missing_xpert_mtb_rif_conducted": missing_xpert_mtb_rif_conducted,
#         "missing_date_sample1_collected": missing_date_sample1_collected,
#         "missing_date_sample1_received": missing_date_sample1_received,
#         "missing_appearance_sample1": missing_appearance_sample1,
#         "missing_sample1_volume": missing_sample1_volume,
#         "missing_invalid_sample1_volume": invalid_sample1_volume.count(),
#         "missing_date_sample2_collected": missing_date_sample2_collected,
#         "missing_date_sample2_received": missing_date_sample2_received,
#         "missing_appearance_sample2": missing_appearance_sample2,
#         "missing_sample2_volume": missing_sample2_volume,
#         "missing_invalid_sample2_volume": invalid_sample2_volume.count(),
#         "missing_sample_reason_when_received_2": missing_sample_reason_when_received_2,
#         "missing_new_reason_when_new_sample_2": missing_new_reason_when_new_sample_2,
#         "missing_other_reason_when_sample_reason_96": missing_other_reason_when_sample_reason_96,
#         "missing_afb_a_date": missing_afb_a_date,
#         "missing_technique_a": missing_technique_a,
#         "missing_afb_a_results": missing_afb_a_results,
#         "missing_afb_b_date": missing_afb_b_date,
#         "missing_technique_b": missing_technique_b,
#         "missing_afb_b_results": missing_afb_b_results,
#         "missing_xpert_date": missing_xpert_date,
#         "missing_xpert_mtb": missing_xpert_mtb,
#         "missing_error_code": missing_error_code,
#         "missing_xpert_rif": missing_xpert_rif,
#         "missing_ct_value": missing_ct_value,
#     }
