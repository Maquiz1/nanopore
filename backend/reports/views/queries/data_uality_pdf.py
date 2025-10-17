from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.apps import apps
import weasyprint

class DataQualityReportPDFView(View):
    """Generate PDF version of the data quality report."""

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
        ).all()

        total_screenings = screenings.count()

        # Serialize function
        def serialize_screening(s):
            zone_name = getattr(getattr(getattr(getattr(s, 'site', None), 'district', None), 'region', None), 'zone', None)
            zone_name = zone_name.name if zone_name else ''
            site_name = getattr(getattr(s, 'site', None), 'name', '')

            clinic_lab_name = getattr(getattr(s, 'clinic_laboratory', None), 'name', '')
            zonal_lab_name = getattr(getattr(s, 'zonal_laboratory', None), 'name', '')
            diagnosis_name = getattr(getattr(s, 'diagnosis', None), 'name', '')

            regimen_missing = False
            regimen_changed = getattr(getattr(s, 'diagnosis', None), 'regimen_changed', False)
            if regimen_changed:
                if not getattr(s, 'regimen_changes', None) or not s.regimen_changes.exists():
                    regimen_missing = True

            xpert_mtb = getattr(getattr(s, 'clinic_laboratory', None), 'xpert_mtb', '')

            tb_treatment_date = getattr(getattr(s, 'diagnosis', None), 'tb_treatment_date', None)
            tb_outcome2 = getattr(getattr(s, 'diagnosis', None), 'tb_outcome2', '')

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
                'regimen_changed': regimen_changed,
                'regimen_missing': regimen_missing,
                'xpert_mtb': xpert_mtb,
                'tb_treatment_date': tb_treatment_date,
                'tb_outcome2': tb_outcome2,
                'months_since_treatment': months_since_treatment
            }

        # Build context
        context = {
            "total_screenings": total_screenings,
            "not_eligible": [serialize_screening(s) for s in screenings.filter(eligible=False)],
            "eligible_not_enrolled": [serialize_screening(s) for s in screenings.filter(eligible=True, enrollment__isnull=True)],
            "enrolled_missing_clinic_laboratory_data": [serialize_screening(s) for s in screenings.filter(eligible=True, clinic_laboratory__isnull=True)],
            "enrolled_missing_diagnosis_data": [serialize_screening(s) for s in screenings.filter(eligible=True, diagnosis__isnull=True)],
            "diagnosis_regimen_changed_missing_regimen": [serialize_screening(s) for s in screenings.filter(
                eligible=True,
                diagnosis__regimen_changed=True
            ).filter(~Q(regimen_changes__isnull=False)).distinct()],
            "enrolled_substudy2_missing_zonal_lab": [serialize_screening(s) for s in screenings.filter(
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2,3,4,5,6],
                zonal_laboratory__isnull=True
            )],
            "pending_outcomes": [serialize_screening(s) for s in screenings.filter(
                diagnosis__tb_treatment=1,
                diagnosis__tb_treatment_date__isnull=False,
                diagnosis__tb_treatment_date__lte=timezone.now().date() - timedelta(days=180)
            )]
        }

        # Calculate months since treatment for pending outcomes
        for s in context['pending_outcomes']:
            if s['tb_treatment_date']:
                delta = timezone.now().date() - s['tb_treatment_date']
                s['months_since_treatment'] = delta.days // 30

        # Render HTML
        html_string = render_to_string(
            'reports/data_quality/data_quality_report.html',  # your template path
            context,
            request=request
        )

        # Generate PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="data_quality_report.pdf"'
        weasyprint.HTML(string=html_string).write_pdf(response)

        return response
