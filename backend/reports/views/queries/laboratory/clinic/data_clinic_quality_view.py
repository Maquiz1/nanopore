# reports/views/mentorships/clinic_data_quality_report_view.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class ClinicDataQualityReportView(View):
    template_name = "reports/data_quality/laboratory/clinic/data_clinic_quality_report.html"

    def get(self, request, *args, **kwargs):
        Clinic = apps.get_model("nanopore", "ClinicLaboratory")

        clinics = Clinic.objects.select_related(
            "screening",
            "screening__site",
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
        ).order_by(
            "screening__site__district__region__zone__name",
            "screening__site__name",
            "screening__pid",
        )

        clinics = filter_queryset_by_user_role(request.user, clinics, site_field="screening__site")

        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        if zone_id:
            clinics = clinics.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            clinics = clinics.filter(screening__site_id=site_id)

        total_clinics = clinics.count()

        def serialize_clinic(c):
            screening = getattr(c, "screening", None)
            zone_obj = getattr(getattr(getattr(getattr(screening, "site", None), "district", None), "region", None), "zone", None)
            return {
                "id": c.id,
                "pid": getattr(screening, "pid", ""),
                "zone_name": zone_obj.name if zone_obj else "",
                "site_name": getattr(getattr(screening, "site", None), "name", ""),
            }

        # explicit querysets (no loops)
        missing_sample_received_qs = clinics.filter(sample_received__isnull=True)

        # --- Q helpers ---
        sample_received_is_2_q = Q(sample_received__value=2) | Q(sample_received__name__iexact="2")
        sample_received_is_1_q = Q(sample_received__value=1) | Q(sample_received__name__iexact="1")
        new_sample_is_1_q = Q(new_sample__value=1) | Q(new_sample__name__iexact="1")
        new_sample_is_2_q = Q(new_sample__value=2) | Q(new_sample__name__iexact="2")
        sample_reason_is_96_q = Q(sample_reason__value=96) | Q(sample_reason__name__iexact="96")

        # number_received required when sample_received in (1,2) OR new_sample == 1
        number_required_q = (sample_received_is_1_q | sample_received_is_2_q | new_sample_is_1_q)
        missing_number_received_qs = clinics.filter(number_required_q, number_received__isnull=True)

        missing_sample_reason_qs = clinics.filter(sample_received_is_2_q, sample_reason__isnull=True)
        missing_new_reason_qs = clinics.filter(new_sample_is_2_q, new_reason__isnull=True)
        missing_other_reason_qs = clinics.filter(sample_reason_is_96_q, other_reason__isnull=True)

        # sample1 when number_received provided
        missing_date_sample1_collected_qs = clinics.filter(number_received__isnull=False, date_sample1_collected__isnull=True)
        missing_date_sample1_received_qs = clinics.filter(number_received__isnull=False, date_sample1_received__isnull=True)
        missing_appearance_sample1_qs = clinics.filter(number_received__isnull=False, appearance_sample1__isnull=True)
        missing_sample1_volume_qs = clinics.filter(number_received__isnull=False, sample1_volume__isnull=True)

        # sample2 when number_received == 2
        nr_is_2_q = Q(number_received__value=2) | Q(number_received__name__iexact="2")
        missing_date_sample2_collected_qs = clinics.filter(nr_is_2_q, date_sample2_collected__isnull=True)
        missing_date_sample2_received_qs = clinics.filter(nr_is_2_q, date_sample2_received__isnull=True)
        missing_appearance_sample2_qs = clinics.filter(nr_is_2_q, appearance_sample2__isnull=True)
        missing_sample2_volume_qs = clinics.filter(nr_is_2_q, sample2_volume__isnull=True)

        # --- Business rule: afb_microscopy_conducted and xpert_mtb_rif_conducted are required when:
        #     sample_received == 1
        #   OR (sample_received == 2 AND new_sample == 1)
        afb_xpert_required_q = sample_received_is_1_q | (sample_received_is_2_q & new_sample_is_1_q)

        # AFB conditional (missing when required by the stricter rule)
        missing_afb_microscopy_conducted_qs = clinics.filter(afb_xpert_required_q, afb_microscopy_conducted__isnull=True)
        afb_yes_q = Q(afb_microscopy_conducted__name__iexact="yes")
        missing_afb_a_date_qs = clinics.filter(afb_yes_q, afb_a_date__isnull=True)
        missing_technique_a_qs = clinics.filter(afb_yes_q, technique_a__isnull=True)
        missing_afb_a_results_qs = clinics.filter(afb_yes_q, afb_a_results__isnull=True)
        missing_afb_b_date_qs = clinics.filter(afb_yes_q, afb_b_date__isnull=True)
        missing_technique_b_qs = clinics.filter(afb_yes_q, technique_b__isnull=True)
        missing_afb_b_results_qs = clinics.filter(afb_yes_q, afb_b_results__isnull=True)
        
        # # 🔹 Group A completeness
        # a_all_missing_q = (
        #     Q(afb_a_date__isnull=True) &
        #     Q(technique_a__isnull=True) &
        #     Q(afb_a_results__isnull=True)
        # )

        # a_all_present_q = (
        #     Q(afb_a_date__isnull=False) &
        #     Q(technique_a__isnull=False) &
        #     Q(afb_a_results__isnull=False)
        # )

        # a_partial_q = (
        #     ~a_all_missing_q & ~a_all_present_q
        # )
        
        # # 🔹 Group B completeness
        # b_all_missing_q = (
        #     Q(afb_b_date__isnull=True) &
        #     Q(technique_b__isnull=True) &
        #     Q(afb_b_results__isnull=True)
        # )

        # b_all_present_q = (
        #     Q(afb_b_date__isnull=False) &
        #     Q(technique_b__isnull=False) &
        #     Q(afb_b_results__isnull=False)
        # )

        # b_partial_q = (
        #     ~b_all_missing_q & ~b_all_present_q
        # )


        # # ✅ FINAL DATA QUALITY QUERIES
        # # ❌ Missing / invalid A
        # missing_afb_a_qs = clinics.filter(
        #     afb_yes_q,
        #     a_partial_q
        # )
        
        # # ❌ Missing / invalid B
        # # B is missing only if A is complete
        # missing_afb_b_qs = clinics.filter(
        #     afb_yes_q,
        #     a_all_present_q,
        #     b_partial_q
        # )
        
        # # ✅ If you still want them split individually
        # missing_afb_b_date_qs = clinics.filter(
        #     afb_yes_q,
        #     a_all_present_q,
        #     b_partial_q,
        #     afb_b_date__isnull=True
        # )

        # missing_technique_b_qs = clinics.filter(
        #     afb_yes_q,
        #     a_all_present_q,
        #     b_partial_q,
        #     technique_b__isnull=True
        # )

        # missing_afb_b_results_qs = clinics.filter(
        #     afb_yes_q,
        #     a_all_present_q,
        #     b_partial_q,
        #     afb_b_results__isnull=True
        # )



        # Xpert conditional (missing when required by the stricter rule)
        missing_xpert_mtb_rif_conducted_qs = clinics.filter(afb_xpert_required_q, xpert_mtb_rif_conducted__isnull=True)
        xpert_yes_q = Q(xpert_mtb_rif_conducted__name__iexact="yes")
        missing_xpert_date_qs = clinics.filter(xpert_yes_q, xpert_date__isnull=True)
        missing_xpert_mtb_qs = clinics.filter(xpert_yes_q, xpert_mtb__isnull=True)

        xpert_in_2_6_q = Q(xpert_mtb__value__in=[2, 3, 4, 5, 6]) | Q(xpert_mtb__name__in=["2", "3", "4", "5", "6"])
        xpert_is_8_q = Q(xpert_mtb__value=8) | Q(xpert_mtb__name__iexact="8")

        missing_error_code_qs = clinics.filter(xpert_is_8_q, error_code__isnull=True)
        missing_xpert_rif_qs = clinics.filter(xpert_in_2_6_q, xpert_rif__isnull=True)
        missing_ct_value_qs = clinics.filter(
            xpert_in_2_6_q
        ).exclude(
            Q(ct_value__isnull=False, ct_na=False) | Q(ct_value__isnull=True, ct_na=True) | Q(ct_value__in=[99, 99.0])
        )

        role_context = get_role_context(request.user)

        context = {
            "total_clinics": total_clinics,
            "report_date": timezone.now(),
            "report_title": "Clinic Laboratory Data Quality Report",
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",

            # lists (limited to 100) - consistent serialization
            "missing_sample_received": [serialize_clinic(c) for c in missing_sample_received_qs[:100]],
            "missing_number_received": [serialize_clinic(c) for c in missing_number_received_qs[:100]],
            "missing_sample_reason_when_received_2": [serialize_clinic(c) for c in missing_sample_reason_qs[:100]],
            "missing_new_reason_when_new_sample_2": [serialize_clinic(c) for c in missing_new_reason_qs[:100]],
            "missing_other_reason_when_sample_reason_96": [serialize_clinic(c) for c in missing_other_reason_qs[:100]],

            "missing_date_sample1_collected": [serialize_clinic(c) for c in missing_date_sample1_collected_qs[:100]],
            "missing_date_sample1_received": [serialize_clinic(c) for c in missing_date_sample1_received_qs[:100]],
            "missing_appearance_sample1": [serialize_clinic(c) for c in missing_appearance_sample1_qs[:100]],
            "missing_sample1_volume": [serialize_clinic(c) for c in missing_sample1_volume_qs[:100]],

            "missing_date_sample2_collected": [serialize_clinic(c) for c in missing_date_sample2_collected_qs[:100]],
            "missing_date_sample2_received": [serialize_clinic(c) for c in missing_date_sample2_received_qs[:100]],
            "missing_appearance_sample2": [serialize_clinic(c) for c in missing_appearance_sample2_qs[:100]],
            "missing_sample2_volume": [serialize_clinic(c) for c in missing_sample2_volume_qs[:100]],

            "missing_afb_microscopy_conducted": [serialize_clinic(c) for c in missing_afb_microscopy_conducted_qs[:100]],
            "missing_afb_a_date": [serialize_clinic(c) for c in missing_afb_a_date_qs[:100]],
            "missing_technique_a": [serialize_clinic(c) for c in missing_technique_a_qs[:100]],
            "missing_afb_a_results": [serialize_clinic(c) for c in missing_afb_a_results_qs[:100]],
            "missing_afb_b_date": [serialize_clinic(c) for c in missing_afb_b_date_qs[:100]],
            "missing_technique_b": [serialize_clinic(c) for c in missing_technique_b_qs[:100]],
            "missing_afb_b_results": [serialize_clinic(c) for c in missing_afb_b_results_qs[:100]],

            "missing_xpert_mtb_rif_conducted": [serialize_clinic(c) for c in missing_xpert_mtb_rif_conducted_qs[:100]],
            "missing_xpert_date": [serialize_clinic(c) for c in missing_xpert_date_qs[:100]],
            "missing_xpert_mtb": [serialize_clinic(c) for c in missing_xpert_mtb_qs[:100]],
            "missing_error_code": [serialize_clinic(c) for c in missing_error_code_qs[:100]],
            "missing_xpert_rif": [serialize_clinic(c) for c in missing_xpert_rif_qs[:100]],
            "missing_ct_value": [serialize_clinic(c) for c in missing_ct_value_qs[:100]],
        }

        # counts
        context.update({
            "count_missing_sample_received": missing_sample_received_qs.count(),
            "count_missing_number_received": missing_number_received_qs.count(),
            "count_missing_sample_reason_when_received_2": missing_sample_reason_qs.count(),
            "count_missing_new_reason_when_new_sample_2": missing_new_reason_qs.count(),
            "count_missing_other_reason_when_sample_reason_96": missing_other_reason_qs.count(),

            "count_missing_date_sample1_collected": missing_date_sample1_collected_qs.count(),
            "count_missing_date_sample1_received": missing_date_sample1_received_qs.count(),
            "count_missing_appearance_sample1": missing_appearance_sample1_qs.count(),
            "count_missing_sample1_volume": missing_sample1_volume_qs.count(),

            "count_missing_date_sample2_collected": missing_date_sample2_collected_qs.count(),
            "count_missing_date_sample2_received": missing_date_sample2_received_qs.count(),
            "count_missing_appearance_sample2": missing_appearance_sample2_qs.count(),
            "count_missing_sample2_volume": missing_sample2_volume_qs.count(),

            "count_missing_afb_microscopy_conducted": missing_afb_microscopy_conducted_qs.count(),
            "count_missing_afb_a_date": missing_afb_a_date_qs.count(),
            "count_missing_technique_a": missing_technique_a_qs.count(),
            "count_missing_afb_a_results": missing_afb_a_results_qs.count(),
            "count_missing_afb_b_date": missing_afb_b_date_qs.count(),
            "count_missing_technique_b": missing_technique_b_qs.count(),
            "count_missing_afb_b_results": missing_afb_b_results_qs.count(),

            "count_missing_xpert_mtb_rif_conducted": missing_xpert_mtb_rif_conducted_qs.count(),
            "count_missing_xpert_date": missing_xpert_date_qs.count(),
            "count_missing_xpert_mtb": missing_xpert_mtb_qs.count(),
            "count_missing_error_code": missing_error_code_qs.count(),
            "count_missing_xpert_rif": missing_xpert_rif_qs.count(),
            "count_missing_ct_value": missing_ct_value_qs.count(),
        })

        # aggregate clinic_report_total (auto-sum of all count_missing_ keys)
        clinic_report_total = sum(
            value for key, value in context.items() if key.startswith("count_missing_") and isinstance(value, int)
        )
        context["clinic_report_total"] = clinic_report_total

        return render(request, self.template_name, context)
