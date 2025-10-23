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
    Data Quality Report for Enrollment model:
    - Checks missing required fields
    - Role-based filtering
    """

    template_name = "reports/data_quality/enrollments/data_enrollment_quality_report.html"

    def get(self, request, *args, **kwargs):
        Enrollment = apps.get_model('nanopore', 'Enrollment')

        # --- Base QuerySet ---
        enrollments = Enrollment.objects.select_related(
            'screening', 'cough2weeks', 'poor_weight', 'coughing_blood',
            'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
            'tx_previous', 'tb_category', 'dr_ds', 'tb_regimen', 'tb_otcome',
            'hiv_status', 'other_diseases', 'sputum_collected'
        ).order_by('-enrollment_date')

        # --- Role-Based Filtering ---
        enrollments = filter_queryset_by_user_role(request.user, enrollments, site_field="screening__site")

        total_enrollments = enrollments.count()

        # --- Missing Fields Check ---
        missing_fields_records = []
        required_fields = [
            'enrollment_date', 'cough2weeks', 'poor_weight', 'coughing_blood',
            'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
            'date_information_collected', 'tx_previous'
        ]

        for e in enrollments:
            missing_fields = []
            for field in required_fields:
                if not getattr(e, field):
                    missing_fields.append(field)
            if missing_fields:
                missing_fields_records.append({
                    'enrollment_id': e.id,
                    'screening_pid': getattr(e.screening, 'pid', ''),
                    'missing_fields': missing_fields,
                })

        # --- Role Context ---
        role_context = get_role_context(request.user)
        is_admin = role_context.get("is_admin", False)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_reviewer = role_context.get("is_reviewer", False)
        is_site_only = role_context.get("is_site_only", False)

        # --- Context for Template ---
        context = {
            "total_enrollments": total_enrollments,
            "missing_fields_records": missing_fields_records,
            "report_date": timezone.now(),
            "is_admin": is_admin,
            "is_zonal_lab": is_zonal_lab,
            "is_reviewer": is_reviewer,
            "is_site_only": is_site_only,
            "enrollment_report_total": len(missing_fields_records),
        }

        return render(request, self.template_name, context)
