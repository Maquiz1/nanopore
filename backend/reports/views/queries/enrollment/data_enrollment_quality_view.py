# views.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class EnrollmentDataQualityReportView(View):
    """
    Detailed data quality report for Enrollment records.

    ✔ provides both queryset + count
    ✔ template-safe
    ✔ matches enrollment_report_total context processor
    """

    template_name = "reports/data_quality/enrollments/data_enrollment_quality_report.html"

    def get(self, request, *args, **kwargs):

        Enrollment = apps.get_model("nanopore", "Enrollment")

        enrollments = Enrollment.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district__region__zone",
        ).order_by(
            "screening__site__district__region__zone__name",
            "screening__site__name",
            "screening__pid",
        )

        enrollments = filter_queryset_by_user_role(
            request.user,
            enrollments,
            site_field="screening__site",
        )

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

        missing_diseases_medical_qs = enrollments.filter(
            other_diseases=1,
            diseases_medical__isnull=True,
        )

        missing_diseases_specify_qs = enrollments.filter(
            diseases_medical=96,
            diseases_specify__isnull=True,
        )

        # =====================================================
        # TB TREATMENT
        # =====================================================

        missing_dr_ds_qs = enrollments.filter(tx_previous=1, dr_ds__isnull=True)
        missing_tb_regimen_qs = enrollments.filter(tx_previous=1, tb_regimen__isnull=True)
        missing_tb_outcome_qs = enrollments.filter(tx_previous=1, tb_otcome__isnull=True)

        missing_tb_regimen_specify_qs = enrollments.filter(
            tb_regimen__value=96,
            tb_regimen_specify__isnull=True,
        )

        missing_tb_regimen_specify_8_qs = enrollments.filter(
            tb_regimen=8,
            tb_regimen_specify__isnull=True,
        )

        missing_tb_category_specify_qs = enrollments.filter(
            tb_category=96,
            tb_category_specify__isnull=True,
        )

        invalid_ltf_months_qs = enrollments.filter(
            tb_category__in=[2, 3]
        ).exclude(
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
        ).exclude(
            Q(tx_month__isnull=True) | Q(tx_month=99)
        )

        missing_tx_year_without_unknown_qs = previous_tx.filter(
            tx_year__isnull=True,
            tx_unknown_year=False,
        )

        invalid_tx_year_with_unknown_qs = previous_tx.filter(
            tx_unknown_year=True
        ).exclude(
            Q(tx_year__isnull=True) | Q(tx_year=99)
        )

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
        ).exclude(
            regimen_months__isnull=True
        )

        # =====================================================
        # TOTAL ISSUES
        # =====================================================

        total_issues = sum([
            missing_hiv_status_qs.count(),
            missing_other_diseases_qs.count(),
            missing_sputum_collected_qs.count(),
            missing_sputum_date_qs.count(),
            missing_sputum_reasons_qs.count(),
            missing_diseases_medical_qs.count(),
            missing_diseases_specify_qs.count(),

            missing_dr_ds_qs.count(),
            missing_tb_regimen_qs.count(),
            missing_tb_outcome_qs.count(),

            missing_tb_regimen_specify_qs.count(),
            missing_tb_regimen_specify_8_qs.count(),
            missing_tb_category_specify_qs.count(),
            invalid_ltf_months_qs.count(),

            missing_tx_month_without_unknown_qs.count(),
            invalid_tx_month_with_unknown_qs.count(),
            missing_tx_year_without_unknown_qs.count(),
            invalid_tx_year_with_unknown_qs.count(),
            invalid_unknown_year_dependencies_qs.count(),

            missing_regimen_months_without_unknown_qs.count(),
            invalid_regimen_months_with_unknown_qs.count(),
        ])

        role_context = get_role_context(request.user)

        context = {
            "report_date": timezone.now(),
            "total_enrollments": enrollments.count(),
            "total_issues": total_issues,
            "enrollment_report_total": total_issues,

            # querysets (safe for {% for %})
            "missing_hiv_status": missing_hiv_status_qs,
            "missing_other_diseases": missing_other_diseases_qs,
            "missing_sputum_collected": missing_sputum_collected_qs,
            "missing_sputum_date": missing_sputum_date_qs,
            "missing_sputum_reasons": missing_sputum_reasons_qs,
            "missing_diseases_medical": missing_diseases_medical_qs,
            "missing_diseases_specify": missing_diseases_specify_qs,

            "missing_dr_ds": missing_dr_ds_qs,
            "missing_tb_regimen": missing_tb_regimen_qs,
            "missing_tb_outcome": missing_tb_outcome_qs,

            "missing_tb_regimen_specify": missing_tb_regimen_specify_qs,
            "missing_tb_regimen_specify_8": missing_tb_regimen_specify_8_qs,
            "missing_tb_category_specify": missing_tb_category_specify_qs,

            "invalid_ltf_months": invalid_ltf_months_qs,

            "missing_tx_month_without_unknown": missing_tx_month_without_unknown_qs,
            "invalid_tx_month_with_unknown": invalid_tx_month_with_unknown_qs,
            "missing_tx_year_without_unknown": missing_tx_year_without_unknown_qs,
            "invalid_tx_year_with_unknown": invalid_tx_year_with_unknown_qs,
            "invalid_unknown_year_dependencies": invalid_unknown_year_dependencies_qs,

            "missing_regimen_months_without_unknown": missing_regimen_months_without_unknown_qs,
            "invalid_regimen_months_with_unknown": invalid_regimen_months_with_unknown_qs,

            # role flags
            **role_context,
        }

        return render(request, self.template_name, context)
