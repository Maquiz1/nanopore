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
    Matches the counting style used in enrollment_report_total context processor.
    """
    template_name = "reports/data_quality/enrollments/data_enrollment_quality_report.html"

    def get(self, request, *args, **kwargs):
        Enrollment = apps.get_model('nanopore', 'Enrollment')

        enrollments = Enrollment.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district__region__zone",
        ).order_by(
            "screening__site__district__region__zone__name",
            "screening__site__name",
            "screening__pid",
        )

        # Apply user role-based filtering
        enrollments = filter_queryset_by_user_role(
            request.user,
            enrollments,
            site_field="screening__site"
        )        

        total_enrollments = enrollments.count()

        # ── Explicit missing / conditional field querysets ─────────
        missing_hiv_status = enrollments.filter(hiv_status__isnull=True)
        missing_other_diseases = enrollments.filter(other_diseases__isnull=True)
        missing_sputum_collected = enrollments.filter(sputum_collected__isnull=True)

        missing_sputum_date = enrollments.filter(sputum_collected=1, sputum_date__isnull=True)
        missing_sputum_reasons = enrollments.filter(sputum_collected=2, sputum_reasons__isnull=True)

        missing_diseases_medical = enrollments.filter(other_diseases=1, diseases_medical__isnull=True)
        missing_diseases_specify = enrollments.filter(diseases_medical=96, diseases_specify__isnull=True)

        missing_tx_year = enrollments.filter(tx_year__isnull=True)
        missing_dr_ds = enrollments.filter(dr_ds__isnull=True)
        missing_ltf_months = enrollments.filter(regimen_months__isnull=True)
        missing_tb_regimen = enrollments.filter(tb_regimen__isnull=True)
        missing_regimen_months = enrollments.filter(regimen_months__isnull=True)
        missing_tb_outcome = enrollments.filter(tb_otcome__isnull=True)

        missing_tb_regimen_specify = enrollments.filter(tb_regimen=96, tb_regimen_specify__isnull=True)
        missing_tb_regimen_specify_8 = enrollments.filter(tb_regimen=8, tb_regimen_specify__isnull=True)
        missing_tb_category_specify = enrollments.filter(tb_category=96, tb_category_specify__isnull=True)

        # Invalid / inconsistent fields
        invalid_ltf_months = enrollments.filter(
            tb_category__in=[2, 3]
        ).exclude(
            Q(ltf_months__isnull=False, ltf_months_unknown=False) |
            Q(ltf_months__isnull=True, ltf_months_unknown=True)
        )

        previous_tx = enrollments.filter(tx_previous=1)
        missing_tx_month_without_unknown = previous_tx.filter(tx_month__isnull=True, tx_unknown_month=False)
        invalid_tx_month_with_unknown = previous_tx.filter(tx_unknown_month=True).exclude(Q(tx_month__isnull=True) | Q(tx_month=99))
        missing_tx_year_without_unknown = previous_tx.filter(tx_year__isnull=True, tx_unknown_year=False)
        invalid_tx_year_with_unknown = previous_tx.filter(tx_unknown_year=True).exclude(Q(tx_year__isnull=True) | Q(tx_year=99))
        invalid_unknown_year_dependencies = previous_tx.filter(tx_unknown_year=True).exclude(Q(tx_month__isnull=True) | Q(tx_month=99), tx_unknown_month=True)
        missing_regimen_months_without_unknown = previous_tx.filter(regimen_months__isnull=True, regimen_months_unknown=False)
        invalid_regimen_months_with_unknown = previous_tx.filter(regimen_months_unknown=True).exclude(Q(regimen_months__isnull=True))

        # ── Total issues ───────────────────────────────────────
        total_issues = sum([
            missing_hiv_status.count(),
            missing_other_diseases.count(),
            missing_sputum_collected.count(),
            missing_sputum_date.count(),
            missing_sputum_reasons.count(),
            missing_diseases_medical.count(),
            missing_diseases_specify.count(),
            missing_tx_year.count(),
            missing_dr_ds.count(),
            missing_ltf_months.count(),
            missing_tb_regimen.count(),
            missing_regimen_months.count(),
            missing_tb_outcome.count(),
            missing_tb_regimen_specify.count(),
            missing_tb_regimen_specify_8.count(),
            missing_tb_category_specify.count(),
            invalid_ltf_months.count(),
            missing_tx_month_without_unknown.count(),
            invalid_tx_month_with_unknown.count(),
            missing_tx_year_without_unknown.count(),
            invalid_tx_year_with_unknown.count(),
            invalid_unknown_year_dependencies.count(),
            missing_regimen_months_without_unknown.count(),
            invalid_regimen_months_with_unknown.count(),
        ])

        role_context = get_role_context(request.user)

        context = {
            "report_date": timezone.now(),
            "total_enrollments": total_enrollments,
            "total_issues": total_issues,
            "enrollment_report_total": total_issues,  # for navbar consistency

            # Individual querysets (template can loop over these)
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

            # Role flags
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_site_only": role_context.get("is_site_only", False),
        }

        return render(request, self.template_name, context)
