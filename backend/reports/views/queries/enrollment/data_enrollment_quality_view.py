# views.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q, Count

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class EnrollmentDataQualityReportView(View):
    """
    Detailed data quality report for Enrollment records.

    ✔ provides both queryset + count
    ✔ template-safe
    ✔ matches enrollment_report_total context processor
    """

    template_name = (
        "reports/data_quality/enrollments/data_enrollment_quality_report.html"
    )

    def get(self, request, *args, **kwargs):

        Enrollment = apps.get_model("nanopore", "Enrollment")

        enrollments = (
            Enrollment.objects.select_related(
                "screening",
                "screening__site",
                "screening__site__district__region__zone",
                "hiv_status",
                "other_diseases",
                "tb_regimen",
                "tb_category",
            )
            .prefetch_related(
                "diseases_medical",
            )
            .order_by(
                "screening__site__district__region__zone__name",
                "screening__site__name",
                "screening__pid",
            )
        )

        role_context = get_role_context(request.user)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_admin = role_context.get("is_admin", False)
        is_reviewer = role_context.get("is_reviewer", False)
        is_superuser = request.user.is_superuser
        is_full_access = is_admin or is_superuser
        is_privileged = is_admin or is_reviewer
        # =====================================================
        # Zones and Sites for filters
        # =====================================================

        enrollments = filter_queryset_by_user_role(
            request.user,
            enrollments,
            site_field="screening__site",
        )

        # Prepare zone and site mappings for template
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # After getting zone_id and site_id from GET
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        # Convert to int if possible
        zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id_int = int(site_id) if site_id and site_id.isdigit() else None

        # Resolve names for template
        selected_zone_name = zones.get(zone_id_int, "") if zone_id_int else ""
        selected_site_name = sites.get(site_id_int, "") if site_id_int else ""

        if zone_id_int:
            enrollments = enrollments.filter(
                screening__site__district__region__zone_id=zone_id_int
            )

        if site_id_int:
            enrollments = enrollments.filter(screening__site_id=site_id_int)

        # =====================================================
        # BASIC REQUIRED FIELDS
        # =====================================================

        missing_hiv_status_qs = enrollments.filter(hiv_status__isnull=True)
        missing_other_diseases_qs = enrollments.filter(other_diseases__isnull=True)
        missing_sputum_collected_qs = enrollments.filter(sputum_collected__isnull=True)

        missing_sputum_date_qs = enrollments.filter(
            sputum_collected=1,
            sputum_date__isnull=True,
        )

        missing_sputum_reasons_qs = enrollments.filter(
            sputum_collected=2,
            sputum_reasons__isnull=True,
        )

        # Many to Many
        missing_diseases_medical_qs = (
            enrollments.filter(other_diseases=1)
            .annotate(diseases_medical_count=Count("diseases_medical", distinct=True))
            .filter(diseases_medical_count=0)
        )

        missing_diseases_specify_qs = enrollments.filter(
            diseases_medical__value=96,
            diseases_specify__isnull=True,
        ).distinct()

        # =====================================================
        # TB TREATMENT
        # =====================================================

        missing_dr_ds_qs = enrollments.filter(tx_previous=1, dr_ds__isnull=True)
        missing_tb_regimen_qs = enrollments.filter(
            tx_previous=1, tb_regimen__isnull=True
        )
        missing_tb_outcome_qs = enrollments.filter(
            tx_previous=1, tb_otcome__isnull=True
        )

        missing_tb_regimen_specify_qs = enrollments.filter(
            tb_regimen__value=96,
            tb_regimen_specify__isnull=True,
        )

        missing_tb_regimen_specify_8_qs = enrollments.filter(
            tb_regimen=8,
            tb_regimen_specify__isnull=True,
        )

        missing_tb_category_specify_qs = enrollments.filter(
            tb_category__value=96,
            tb_category_specify__isnull=True,
        )

        invalid_ltf_months_qs = enrollments.filter(tb_category__in=[2, 3]).exclude(
            Q(ltf_months__isnull=False, ltf_months_unknown=False)
            | Q(ltf_months__isnull=True, ltf_months_unknown=True)
        )

        # =====================================================
        # PREVIOUS TB TREATMENT LOGIC
        # =====================================================

        previous_tx = enrollments.filter(tx_previous=1)

        missing_tx_month_without_unknown_qs = previous_tx.filter(
            tx_month__isnull=True,
            tx_unknown_month=False,
        )

        invalid_tx_month_with_unknown_qs = previous_tx.filter(
            tx_unknown_month=True
        ).exclude(Q(tx_month__isnull=True) | Q(tx_month=99))

        missing_tx_year_without_unknown_qs = previous_tx.filter(
            tx_year__isnull=True,
            tx_unknown_year=False,
        )

        invalid_tx_year_with_unknown_qs = previous_tx.filter(
            tx_unknown_year=True
        ).exclude(Q(tx_year__isnull=True) | Q(tx_year=99))

        invalid_unknown_year_dependencies_qs = previous_tx.filter(
            tx_unknown_year=True
        ).exclude(
            Q(tx_month__isnull=True) | Q(tx_month=99),
            tx_unknown_month=True,
        )

        missing_regimen_months_without_unknown_qs = previous_tx.filter(
            regimen_months__isnull=True,
            regimen_months_unknown=False,
        )

        invalid_regimen_months_with_unknown_qs = previous_tx.filter(
            regimen_months_unknown=True
        ).exclude(regimen_months__isnull=True)

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
        missing_tx_previous_2_3_tb_filled_qs = enrollments.filter(
            tx_previous_2_3_q
        ).filter(
            tb_fields_filled_q | unknown_true_q
        )

        count_missing_tx_previous_2_3_tb_filled = missing_tx_previous_2_3_tb_filled_qs.count()

        # ─────────────────────────────────────────────
        # Prepare context
        # ─────────────────────────────────────────────
        context = {
            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id or "",
            "selected_site": site_id or "",
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,
            "report_date": timezone.now(),
            "total_enrollment_records": enrollments.count(),
            # querysets (safe for {% for %})
            "missing_hiv_status": missing_hiv_status_qs,
            "count_missing_hiv_status": missing_hiv_status_qs.count(),
            "missing_other_diseases": missing_other_diseases_qs,
            "count_missing_other_diseases": missing_other_diseases_qs.count(),
            "missing_sputum_collected": missing_sputum_collected_qs,
            "count_missing_sputum_collected": missing_sputum_collected_qs.count(),
            "missing_sputum_date": missing_sputum_date_qs,
            "count_missing_sputum_date": missing_sputum_date_qs.count(),
            "missing_sputum_reasons": missing_sputum_reasons_qs,
            "count_missing_sputum_reasons": missing_sputum_reasons_qs.count(),
            "missing_diseases_medical": missing_diseases_medical_qs,
            "count_missing_diseases_medical": missing_diseases_medical_qs.count(),
            "missing_diseases_specify": missing_diseases_specify_qs,
            "count_missing_diseases_specify": missing_diseases_specify_qs.count(),
            "missing_dr_ds": missing_dr_ds_qs,
            "count_missing_dr_ds": missing_dr_ds_qs.count(),
            "missing_tb_regimen": missing_tb_regimen_qs,
            "count_missing_tb_regimen": missing_tb_regimen_qs.count(),
            "missing_tb_outcome": missing_tb_outcome_qs,
            "count_missing_tb_outcome": missing_tb_outcome_qs.count(),
            "missing_tb_regimen_specify": missing_tb_regimen_specify_qs,
            "count_missing_tb_regimen_specify": missing_tb_regimen_specify_qs.count(),
            "missing_tb_regimen_specify_8": missing_tb_regimen_specify_8_qs,
            "count_missing_tb_regimen_specify_8": missing_tb_regimen_specify_8_qs.count(),
            "missing_tb_category_specify": missing_tb_category_specify_qs,
            "count_missing_tb_category_specify": missing_tb_category_specify_qs.count(),
            "invalid_ltf_months": invalid_ltf_months_qs,
            "count_invalid_ltf_months": invalid_ltf_months_qs.count(),
            "missing_tx_month_without_unknown": missing_tx_month_without_unknown_qs,
            "count_missing_tx_month_without_unknown": missing_tx_month_without_unknown_qs.count(),
            "invalid_tx_month_with_unknown": invalid_tx_month_with_unknown_qs,
            "count_invalid_tx_month_with_unknown": invalid_tx_month_with_unknown_qs.count(),
            "missing_tx_year_without_unknown": missing_tx_year_without_unknown_qs,
            "count_missing_tx_year_without_unknown": missing_tx_year_without_unknown_qs.count(),
            "invalid_tx_year_with_unknown": invalid_tx_year_with_unknown_qs,
            "count_invalid_tx_year_with_unknown": invalid_tx_year_with_unknown_qs.count(),
            "invalid_unknown_year_dependencies": invalid_unknown_year_dependencies_qs,
            "count_invalid_unknown_year_dependencies": invalid_unknown_year_dependencies_qs.count(),
            "missing_regimen_months_without_unknown": missing_regimen_months_without_unknown_qs,
            "count_missing_regimen_months_without_unknown": missing_regimen_months_without_unknown_qs.count(),
            "invalid_regimen_months_with_unknown": invalid_regimen_months_with_unknown_qs,
            "count_invalid_regimen_months_with_unknown": invalid_regimen_months_with_unknown_qs.count(),
            
            "missing_tx_previous_2_3_tb_filled": missing_tx_previous_2_3_tb_filled_qs,
            "count_missing_tx_previous_2_3_tb_filled": count_missing_tx_previous_2_3_tb_filled,

        }

        # Total issues
        context["total_enrollment_issues"] = sum(
            [
                context["count_missing_hiv_status"],
                context["count_missing_other_diseases"],
                context["count_missing_sputum_collected"],
                context["count_missing_sputum_date"],
                context["count_missing_sputum_reasons"],
                context["count_missing_diseases_medical"],
                context["count_missing_diseases_specify"],
                context["count_missing_dr_ds"],
                context["count_missing_tb_regimen"],
                context["count_missing_tb_outcome"],
                context["count_missing_tb_regimen_specify"],
                context["count_missing_tb_regimen_specify_8"],
                context["count_missing_tb_category_specify"],
                context["count_invalid_ltf_months"],
                # ✅ NEW
                context["count_missing_tx_month_without_unknown"],
                context["count_invalid_tx_month_with_unknown"],
                context["count_missing_tx_year_without_unknown"],
                context["count_invalid_tx_year_with_unknown"],
                context["count_invalid_unknown_year_dependencies"],
                context["count_missing_regimen_months_without_unknown"],
                context["count_invalid_regimen_months_with_unknown"],
                context["count_missing_tx_previous_2_3_tb_filled"],
            ]
        )

        return render(request, self.template_name, context)

