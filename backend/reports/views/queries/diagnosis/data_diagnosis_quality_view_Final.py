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

        # ─────────────────────────────────────────────
        # Base queryset
        # ─────────────────────────────────────────────
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
            request.user, diagnoses, site_field="screening__site"
        )

        # ─────────────────────────────────────────────
        # MISSING CORE FIELDS / CONDITIONAL RULES
        # ─────────────────────────────────────────────

        missing_tb_diagnosis = diagnoses.filter(tb_diagnosis__isnull=True)
        missing_tb_diagnosis_date = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_date__isnull=True)
        missing_tb_diagnosis_made = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made__isnull=True)
        missing_tb_treatment = diagnoses.filter(tb_diagnosis=1, tb_treatment__isnull=True)
        missing_diagnosis_made_other = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=96, diagnosis_made_other__isnull=True)
        missing_tb_diagnosed_clinically = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=1, tb_diagnosed_clinically__isnull=True)
        missing_tb_clinically_other = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=1, tb_diagnosed_clinically__id=96, tb_clinically_other__isnull=True)
        missing_bacteriological_diagnosis = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=2, bacteriological_diagnosis__isnull=True)
        missing_clinician_received_date = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=2, clinician_received_date__isnull=True)

        missing_tb_other_diagnosis = diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis__isnull=True)
        missing_tb_diagnosis_made2 = diagnoses.filter(tb_diagnosis=2, tb_diagnosis_made2__isnull=True)
        missing_tb_other_specify = diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis=96, tb_other_specify__isnull=True)

        missing_tb_treatment_date = diagnoses.filter(tb_treatment=1, tb_treatment_date__isnull=True)
        missing_tb_register_number = diagnoses.filter(tb_treatment=1, tb_register_number__isnull=True)
        missing_tb_regimen = diagnoses.filter(tb_treatment=1, tb_regimen__isnull=True)
        missing_regimen_changed = diagnoses.filter(tb_treatment=1, regimen_changed__isnull=True)
        missing_tb_facility = diagnoses.filter(tb_treatment=2, tb_facility__isnull=True)
        missing_tb_reason = diagnoses.filter(tb_treatment=96, tb_reason__isnull=True)
        missing_tb_outcome2_date = diagnoses.filter(tb_outcome2__in=[1, 2, 3, 4, 5], tb_outcome2_date__isnull=True)

        # ─────────────────────────────────────────────
        # ≥ 6 MONTHS TREATMENT CHECK
        # ─────────────────────────────────────────────
        six_months_ago = timezone.now().date() - timedelta(days=180)
        long_treatment = diagnoses.filter(tb_treatment=1, tb_treatment_date__lte=six_months_ago)

        pending_tb_outcome = long_treatment.filter(tb_outcome2__isnull=True)
        pending_tb_outcome_date = long_treatment.filter(tb_outcome2__in=[1, 2, 3, 4, 5], tb_outcome2_date__isnull=True)

        # ─────────────────────────────────────────────
        # TOTAL ISSUES
        # ─────────────────────────────────────────────
        total_issues = (
            missing_tb_diagnosis.count()
            + missing_tb_diagnosis_date.count()
            + missing_tb_diagnosis_made.count()
            + missing_tb_treatment.count()
            + missing_diagnosis_made_other.count()
            + missing_tb_diagnosed_clinically.count()
            + missing_tb_clinically_other.count()
            + missing_bacteriological_diagnosis.count()
            + missing_clinician_received_date.count()
            + missing_tb_other_diagnosis.count()
            + missing_tb_diagnosis_made2.count()
            + missing_tb_other_specify.count()
            + missing_tb_treatment_date.count()
            + missing_tb_register_number.count()
            + missing_tb_regimen.count()
            + missing_regimen_changed.count()
            + missing_tb_facility.count()
            + missing_tb_reason.count()
            + missing_tb_outcome2_date.count()
            + pending_tb_outcome.count()
            + pending_tb_outcome_date.count()
        )

        # ─────────────────────────────────────────────
        # CONTEXT
        # ─────────────────────────────────────────────
        context = {
            "report_date": timezone.now(),
            "total_diagnosis_records": diagnoses.count(),
            "total_diagnosis_issues": total_issues,

            "missing_tb_diagnosis": missing_tb_diagnosis,
            "count_missing_tb_diagnosis": missing_tb_diagnosis.count(),

            "missing_tb_diagnosis_date": missing_tb_diagnosis_date,
            "count_missing_tb_diagnosis_date": missing_tb_diagnosis_date.count(),

            "missing_tb_diagnosis_made": missing_tb_diagnosis_made,
            "count_missing_tb_diagnosis_made": missing_tb_diagnosis_made.count(),

            "missing_tb_treatment": missing_tb_treatment,
            "count_missing_tb_treatment": missing_tb_treatment.count(),

            "missing_diagnosis_made_other": missing_diagnosis_made_other,
            "count_missing_diagnosis_made_other": missing_diagnosis_made_other.count(),

            "missing_tb_diagnosed_clinically": missing_tb_diagnosed_clinically,
            "count_missing_tb_diagnosed_clinically": missing_tb_diagnosed_clinically.count(),

            "missing_tb_clinically_other": missing_tb_clinically_other,
            "count_missing_tb_clinically_other": missing_tb_clinically_other.count(),

            "missing_bacteriological_diagnosis": missing_bacteriological_diagnosis,
            "count_missing_bacteriological_diagnosis": missing_bacteriological_diagnosis.count(),

            "missing_clinician_received_date": missing_clinician_received_date,
            "count_missing_clinician_received_date": missing_clinician_received_date.count(),

            "missing_tb_other_diagnosis": missing_tb_other_diagnosis,
            "count_missing_tb_other_diagnosis": missing_tb_other_diagnosis.count(),

            "missing_tb_diagnosis_made2": missing_tb_diagnosis_made2,
            "count_missing_tb_diagnosis_made2": missing_tb_diagnosis_made2.count(),

            "missing_tb_other_specify": missing_tb_other_specify,
            "count_missing_tb_other_specify": missing_tb_other_specify.count(),

            "missing_tb_treatment_date": missing_tb_treatment_date,
            "count_missing_tb_treatment_date": missing_tb_treatment_date.count(),

            "missing_tb_register_number": missing_tb_register_number,
            "count_missing_tb_register_number": missing_tb_register_number.count(),

            "missing_tb_regimen": missing_tb_regimen,
            "count_missing_tb_regimen": missing_tb_regimen.count(),

            "missing_regimen_changed": missing_regimen_changed,
            "count_missing_regimen_changed": missing_regimen_changed.count(),

            "missing_tb_facility": missing_tb_facility,
            "count_missing_tb_facility": missing_tb_facility.count(),

            "missing_tb_reason": missing_tb_reason,
            "count_missing_tb_reason": missing_tb_reason.count(),

            "missing_tb_outcome2_date": missing_tb_outcome2_date,
            "count_missing_tb_outcome2_date": missing_tb_outcome2_date.count(),

            "pending_tb_outcome": pending_tb_outcome,
            "count_pending_tb_outcome": pending_tb_outcome.count(),

            "pending_tb_outcome_date": pending_tb_outcome_date,
            "count_pending_tb_outcome_date": pending_tb_outcome_date.count(),
        }

        return render(request, self.template_name, context)
