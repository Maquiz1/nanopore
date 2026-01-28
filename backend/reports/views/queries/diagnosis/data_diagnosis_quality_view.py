from django.views import View
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.apps import apps

from utils.permissions import filter_queryset_by_user_role


class DiagnosisDataQualityReportView(View):
    """
    Diagnosis data quality report
    — fully aligned with diagnosis_report_total context processor
    """

    template_name = "reports/data_quality/diagnosis/data_diagnosis_quality_report.html"

    def get(self, request, *args, **kwargs):

        Diagnosis = apps.get_model("nanopore", "Diagnosis")

        # ─────────────────────────────────────────────────────────────
        # Base queryset
        # ─────────────────────────────────────────────────────────────
        diagnoses = Diagnosis.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district__region__zone",
        ).order_by(
            "screening__site__district__region__zone__name",
            "screening__site__name",
            "screening__pid",
        )

        diagnoses = filter_queryset_by_user_role(
            request.user,
            diagnoses,
            site_field="screening__site"
        )

        # ─────────────────────────────────────────────────────────────
        # Shared logic with navbar
        # ─────────────────────────────────────────────────────────────
        tb_treatment_is_1_q = (
            Q(tb_treatment__value=1)
            | Q(tb_treatment__name__iexact="1")
        )

        # ─────────────────────────────────────────────────────────────
        # Missing core fields
        # ─────────────────────────────────────────────────────────────
        missing_tb_diagnosis = diagnoses.filter(
            tb_diagnosis__isnull=True
        )

        missing_tb_diagnosis_date = diagnoses.filter(
            tb_diagnosis_date__isnull=True
        )

        missing_tb_diagnosis_made = diagnoses.filter(
            tb_diagnosis_made__isnull=True
        )

        missing_bacteriological_diagnosis = diagnoses.filter(
            bacteriological_diagnosis__isnull=True
        )

        missing_tb_treatment = diagnoses.filter(
            tb_treatment__isnull=True
        )

        missing_tb_treatment_date = diagnoses.filter(
            tb_treatment_is_1_q,
            tb_treatment_date__isnull=True
        )

        missing_tb_facility = diagnoses.filter(
            tb_facility__isnull=True
        )

        missing_tb_regimen = diagnoses.filter(
            tb_treatment_is_1_q,
            tb_regimen__isnull=True
        )

        missing_tb_outcome2 = diagnoses.filter(
            tb_outcome2__isnull=True
        )

        missing_tb_outcome2_date = diagnoses.filter(
            tb_outcome2__isnull=False,
            tb_outcome2_date__isnull=True
        )

        # ─────────────────────────────────────────────────────────────
        # ≥ 6 months treatment logic
        # ─────────────────────────────────────────────────────────────
        six_months_ago = timezone.now().date() - timedelta(days=180)

        long_treatment_base = diagnoses.filter(
            tb_treatment_is_1_q,
            tb_treatment_date__isnull=False,
            tb_treatment_date__lte=six_months_ago
        )

        pending_tb_outcome = long_treatment_base.filter(
            tb_outcome2__isnull=True
        )

        pending_tb_outcome_date = long_treatment_base.filter(
            tb_outcome2_date__isnull=True
        )

        # ─────────────────────────────────────────────────────────────
        # Total issue count (same as navbar)
        # ─────────────────────────────────────────────────────────────
        total_issues = (
            missing_tb_diagnosis.count()
            + missing_tb_diagnosis_date.count()
            + missing_tb_diagnosis_made.count()
            + missing_bacteriological_diagnosis.count()
            + missing_tb_treatment.count()
            + missing_tb_treatment_date.count()
            + missing_tb_facility.count()
            + missing_tb_regimen.count()
            + missing_tb_outcome2.count()
            + missing_tb_outcome2_date.count()
            + pending_tb_outcome.count()
            + pending_tb_outcome_date.count()
        )

        # ─────────────────────────────────────────────────────────────
        # Context
        # ─────────────────────────────────────────────────────────────
        context = {
            "report_date": timezone.now(),

            "total_diagnosis_records": diagnoses.count(),
            "total_diagnosis_issues": total_issues,

            # Missing core fields
            "missing_tb_diagnosis": missing_tb_diagnosis,
            "count_missing_tb_diagnosis": missing_tb_diagnosis.count(),

            "missing_tb_diagnosis_date": missing_tb_diagnosis_date,
            "count_missing_tb_diagnosis_date": missing_tb_diagnosis_date.count(),

            "missing_tb_diagnosis_made": missing_tb_diagnosis_made,
            "count_missing_tb_diagnosis_made": missing_tb_diagnosis_made.count(),

            "missing_bacteriological_diagnosis": missing_bacteriological_diagnosis,
            "count_missing_bacteriological_diagnosis": missing_bacteriological_diagnosis.count(),

            "missing_tb_treatment": missing_tb_treatment,
            "count_missing_tb_treatment": missing_tb_treatment.count(),

            "missing_tb_treatment_date": missing_tb_treatment_date,
            "count_missing_tb_treatment_date": missing_tb_treatment_date.count(),

            "missing_tb_facility": missing_tb_facility,
            "count_missing_tb_facility": missing_tb_facility.count(),

            "missing_tb_regimen": missing_tb_regimen,
            "count_missing_tb_regimen": missing_tb_regimen.count(),

            "missing_tb_outcome2": missing_tb_outcome2,
            "count_missing_tb_outcome2": missing_tb_outcome2.count(),

            "missing_tb_outcome2_date": missing_tb_outcome2_date,
            "count_missing_tb_outcome2_date": missing_tb_outcome2_date.count(),

            # ≥ 6 months workflow
            "pending_tb_outcome": pending_tb_outcome,
            "count_pending_tb_outcome": pending_tb_outcome.count(),

            "pending_tb_outcome_date": pending_tb_outcome_date,
            "count_pending_tb_outcome_date": pending_tb_outcome_date.count(),
        }

        return render(request, self.template_name, context)
