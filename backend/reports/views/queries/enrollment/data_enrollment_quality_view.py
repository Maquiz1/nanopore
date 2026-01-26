# views.py
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Q

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

class EnrollmentDataQualityReportView(View):
    template_name = "reports/data_quality/enrollments/data_enrollment_quality_report.html"

    def get(self, request, *args, **kwargs):
        Enrollment = apps.get_model('nanopore', 'Enrollment')

        enrollments = Enrollment.objects.select_related(
            'screening', 'cough2weeks', 'poor_weight', 'coughing_blood',
            'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
            'tx_previous', 'tb_category', 'dr_ds', 'tb_regimen', 'tb_otcome',
            'hiv_status', 'other_diseases', 'sputum_collected'
        ).order_by('-enrollment_date')

        enrollments = filter_queryset_by_user_role(request.user, enrollments, site_field="screening__site")

        total_enrollments = enrollments.count()

        required_fields = [
            'enrollment_date', 'cough2weeks', 'poor_weight', 'coughing_blood',
            'unexplained_fever', 'night_sweats', 'neck_lymph', 'history_tb',
            'date_information_collected', 'tx_previous'
        ]

        # Count per field (fast ORM version)
        from django.db.models import Count, Case, When, Value, IntegerField

        annotations = {}
        for field in required_fields:
            annotations[f"missing_{field}"] = Count(
                Case(
                    When(**{f"{field}__isnull": True}, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )

        # Get counts for summary
        summary = enrollments.aggregate(**annotations)

        # Records with at least one missing field
        missing_fields_records = []
        for e in enrollments.filter(
            **{f"{field}__isnull": True for field in required_fields}  # at least one is null
        )[:150]:  # limit to avoid huge pages
            missing = [f for f in required_fields if not getattr(e, f)]
            if missing:
                missing_fields_records.append({
                    'enrollment_id': e.id,
                    'screening_pid': getattr(e.screening, 'pid', ''),
                    'missing_fields': missing,
                })

        role_context = get_role_context(request.user)

        context = {
            "total_enrollments": total_enrollments,
            "missing_fields_records": missing_fields_records,
            "report_date": timezone.now(),
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_site_only": role_context.get("is_site_only", False),
            "enrollment_report_total": len(missing_fields_records),

            # Per-field counts – useful for dashboard badges
            **{f"count_missing_{field}": summary[f"missing_{field}"] for field in required_fields},
        }

        return render(request, self.template_name, context)