from django.views import View
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, ExpressionWrapper, IntegerField, F
from django.apps import apps

from utils.permissions import filter_queryset_by_user_role


class DiagnosisDataQualityReportView(View):
    """
    Role-aware data quality report focused on Diagnosis model issues.
    Prepares context for the diagnosis-specific template with accordion sections.
    """
    template_name = "reports/data_quality/diagnosis/data_diagnosis_quality_report.html"

    def get(self, request, *args, **kwargs):
        Diagnosis = apps.get_model('nanopore', 'Diagnosis')
        Screening  = apps.get_model('nanopore', 'Screening')

        # ── Base Diagnosis QuerySet ─────────────────────────────────────────────
        diagnoses = Diagnosis.objects.select_related(
            'screening',
            'screening__site',
            'screening__site__district__region__zone',
        ).order_by(
            'screening__site__district__region__zone__name',
            'screening__site__name',
            'screening__pid'
        )

        # Role-based filtering (assuming site is reachable via screening)
        diagnoses = filter_queryset_by_user_role(
            request.user,
            diagnoses,
            site_field="screening__site"
        )

        # Optional GET filters
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        if zone_id:
            diagnoses = diagnoses.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            diagnoses = diagnoses.filter(screening__site_id=site_id)

        total_records = diagnoses.count()

        # ── Define critical missing fields ──────────────────────────────────────
        critical_fields = [
            "tb_diagnosis",
            "tb_diagnosis_date",
            "tb_treatment",
            "tb_treatment_date",
            "tb_regimen",
            # "tb_facility",           # optional – uncomment if critical
            # "bacteriological_diagnosis",
        ]

        # ── Missing individual fields ───────────────────────────────────────────
        missing_tb_diagnosis       = diagnoses.filter(tb_diagnosis__isnull=True)
        missing_tb_diagnosis_date  = diagnoses.filter(tb_diagnosis_date__isnull=True)
        missing_tb_treatment       = diagnoses.filter(tb_diagnosis__isnull=False, tb_treatment__isnull=True)
        missing_tb_treatment_date  = diagnoses.filter(tb_treatment=1, tb_treatment_date__isnull=True)
        missing_tb_regimen         = diagnoses.filter(tb_treatment=1, tb_regimen__isnull=True)

        # ── Pending outcomes (treatment ≥ 6 months ago) ─────────────────────────
        six_months_ago = timezone.now().date() - timedelta(days=180)

        long_treatment = diagnoses.filter(
            tb_treatment=1,
            tb_treatment_date__isnull=False,
            tb_treatment_date__lte=six_months_ago
        ).annotate(
            months_on_treatment=ExpressionWrapper(
                (timezone.now().date() - F('tb_treatment_date')) / 30,
                output_field=IntegerField()
            )
        )

        pending_outcome     = long_treatment.filter(tb_outcome2__isnull=True)
        pending_outcome_date = long_treatment.filter(tb_outcome2_date__isnull=True)

        # ── Calculate total issues ──────────────────────────────────────────────
        # (each record can contribute to multiple categories → we count issues, not unique records)
        total_issues = sum([
            missing_tb_diagnosis.count(),
            missing_tb_diagnosis_date.count(),
            missing_tb_treatment.count(),
            missing_tb_treatment_date.count(),
            missing_tb_regimen.count(),
            pending_outcome.count(),
            pending_outcome_date.count(),
        ])

        # ── Prepare context ─────────────────────────────────────────────────────
        context = {
            "report_date": timezone.now(),

            "total_diagnosis_records": total_records,
            "total_diagnosis_issues":  total_issues,

            # Missing fields sections
            "count_missing_tb_diagnosis":      missing_tb_diagnosis.count(),
            "missing_tb_diagnosis":            missing_tb_diagnosis,

            "count_missing_tb_diagnosis_date": missing_tb_diagnosis_date.count(),
            "missing_tb_diagnosis_date":       missing_tb_diagnosis_date,

            "count_missing_tb_treatment":      missing_tb_treatment.count(),
            "missing_tb_treatment":            missing_tb_treatment,

            # You can add more missing fields here (tb_regimen, tb_facility, etc.)

            # Long-term treatment – outcome missing
            "count_pending_tb_outcome":     pending_outcome.count(),
            "pending_tb_outcome":           pending_outcome,

            "count_pending_tb_outcome_date": pending_outcome_date.count(),
            "pending_tb_outcome_date":       pending_outcome_date,
        }

        # Optional: add zone/site filter choices if needed in template
        # context["zones"] = ... 
        # context["sites"] = ...

        return render(request, self.template_name, context)