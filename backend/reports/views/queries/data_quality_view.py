from django.views import View
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.apps import apps

# -----------------------------
# Main HTML view
# -----------------------------
class DataQualityReportView(View):
    """Generate categorized data quality report for screenings and related models."""

    template_name = "reports/data_quality/data_quality_report.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model('nanopore', 'Screening')

        screenings = Screening.objects.select_related(
            'site',
            'site__district',
            'site__district__region',
            'site__district__region__zone',
            'clinic_laboratory',
            'diagnosis',
            'zonal_laboratory'
        ).order_by(
            'site__district__region__zone__name',
            'site__name',
            'pid'
        ).all()

        total_screenings = screenings.count()

        # Helper to convert screening to dict
        def serialize_screening(s):
            zone_name = getattr(getattr(getattr(getattr(s, 'site', None), 'district', None), 'region', None), 'zone', None)
            zone_name = zone_name.name if zone_name else ''
            site_name = getattr(getattr(s, 'site', None), 'name', '')

            clinic_lab_name = getattr(getattr(s, 'clinic_laboratory', None), 'name', '')
            zonal_lab_name = getattr(getattr(s, 'zonal_laboratory', None), 'name', '')
            diagnosis_name = getattr(getattr(s, 'diagnosis', None), 'name', '')
            eligible = getattr(getattr(s, 'screening', None), 'eligible', '')
            reasons = getattr(getattr(s, 'screening', None), 'reasons', '')
            reasons_other = getattr(getattr(s, 'screening', None), 'reasons_other', '')

            missing_fields = []
            if not clinic_lab_name:
                missing_fields.append("Clinic")
            if not diagnosis_name:
                missing_fields.append("Diagnosis")

            regimen_missing = False
            if getattr(s, 'diagnosis', None) and getattr(s.diagnosis, 'regimen_changed', False):
                if not getattr(s, 'regimen_changes', None) or not s.regimen_changes.exists():
                    regimen_missing = True

            xpert_mtb = getattr(getattr(s, 'clinic_laboratory', None), 'xpert_mtb', '')

            tb_treatment_date = getattr(getattr(s, 'diagnosis', None), 'tb_treatment_date', None)
            tb_outcome2 = getattr(getattr(s, 'diagnosis', None), 'tb_outcome2', '')
            regimen_changed = getattr(getattr(s, 'diagnosis', None), 'regimen_changed', '')

            months_since_treatment = None
            if tb_treatment_date:
                delta = timezone.now().date() - tb_treatment_date
                months_since_treatment = delta.days // 30

            return {
                'pid': getattr(s, 'pid', ''),
                'zone_name': zone_name,
                'site_name': site_name,
                'clinic_lab_name': clinic_lab_name,
                'zonal_lab_name': zonal_lab_name,
                'diagnosis_name': diagnosis_name,
                'missing_fields': missing_fields,  # ✅ list
                'regimen_missing': regimen_missing,
                'xpert_mtb': xpert_mtb,
                'tb_treatment_date': tb_treatment_date,
                'tb_outcome2': tb_outcome2,
                'months_since_treatment': months_since_treatment,
                'regimen_changed': regimen_changed,
                'eligible': eligible,
                'reasons': reasons,
                'reasons_other': reasons_other
            }

        # 6 months ago
        six_months_ago = timezone.now().date() - timedelta(days=180)

        # Step 1: Filter screenings where treatment started more than 6 months ago
        treatment_started_6m_ago = screenings.filter(
            diagnosis__tb_treatment=1,
            diagnosis__tb_treatment_date__isnull=False,
            diagnosis__tb_treatment_date__lte=six_months_ago
        )

        # Step 2: Find screenings with missing outcomes
        pending_tb_outcomes = treatment_started_6m_ago.filter(
            Q(diagnosis__tb_outcome2__isnull=True)
        )

        # Step 3: Find screenings with missing outcome dates
        pending_tb_outcomes_date = treatment_started_6m_ago.filter(
            Q(diagnosis__tb_outcome2_date__isnull=True)
        )

        # Build context
        context = {
            "total_screenings": total_screenings,
            "not_eligible": [serialize_screening(s) for s in screenings.filter(eligible=False)],
            "eligible_not_enrolled": [serialize_screening(s) for s in screenings.filter(eligible=True, enrollment__isnull=True)],
            "enrolled_missing_clinic_laboratory_data": [serialize_screening(s) for s in screenings.filter(eligible=True).filter(
                Q(clinic_laboratory__isnull=True))],
            "enrolled_missing_diagnosis_data": [serialize_screening(s) for s in screenings.filter(eligible=True).filter(
                Q(diagnosis__isnull=True))],
            "diagnosis_regimen_changed_missing_regimen": [serialize_screening(s) for s in screenings.filter(eligible=True, diagnosis__regimen_changed=True).filter(
                ~Q(regimen_changes__isnull=False)).distinct()],
            "enrolled_substudy2_missing_zonal_lab": [serialize_screening(s) for s in screenings.filter(
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2,3,4,5,6],
                zonal_laboratory__isnull=True)],
            # # Step 2: Find screenings with missing outcomes
            # "pending_outcomes": [serialize_screening(s) for s in screenings.filter(
            #     diagnosis__tb_treatment=1,
            #     diagnosis__tb_treatment_date__isnull=False,
            #     diagnosis__tb_treatment_date__lte=six_months_ago)],
            # # Step 3: Find screenings with missing outcomes dates
            # "pending_outcomes_date": [serialize_screening(s) for s in screenings.filter(
            #     diagnosis__tb_treatment=1,
            #     diagnosis__tb_treatment_date__isnull=False,
            #     diagnosis__tb_treatment_date__lte=six_months_ago)]
            "pending_outcomes": [serialize_screening(s) for s in pending_tb_outcomes],
            "pending_outcomes_date": [serialize_screening(s) for s in pending_tb_outcomes_date]
        }

        # Add months since treatment for pending outcomes
        for s in context['pending_outcomes']:
            if s['tb_treatment_date']:
                delta = timezone.now().date() - s['tb_treatment_date']
                s['months_since_treatment'] = delta.days // 30

        return render(request, self.template_name, context)