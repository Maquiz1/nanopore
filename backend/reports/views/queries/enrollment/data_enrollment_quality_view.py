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

        # Base queryset – only select_related what's actually useful
        enrollments = Enrollment.objects.select_related(
            'screening',                # for PID, site, etc.
            'screening__site',
            # Boolean/choice fields usually don't need select_related
        ).order_by('-enrollment_date')

        enrollments = filter_queryset_by_user_role(
            request.user,
            enrollments,
            site_field="screening__site"
        )

        total_enrollments = enrollments.count()

        # ── Explicit missing field counts (matches context processor style) ─────
        missing_enrollment_date          = enrollments.filter(enrollment_date__isnull=True).count()
        missing_cough2weeks              = enrollments.filter(cough2weeks__isnull=True).count()
        missing_poor_weight              = enrollments.filter(poor_weight__isnull=True).count()
        missing_coughing_blood           = enrollments.filter(coughing_blood__isnull=True).count()
        missing_unexplained_fever        = enrollments.filter(unexplained_fever__isnull=True).count()
        missing_night_sweats             = enrollments.filter(night_sweats__isnull=True).count()
        missing_neck_lymph               = enrollments.filter(neck_lymph__isnull=True).count()
        missing_history_tb               = enrollments.filter(history_tb__isnull=True).count()
        missing_date_information_collected = enrollments.filter(date_information_collected__isnull=True).count()
        missing_tx_previous              = enrollments.filter(tx_previous__isnull=True).count()

        # Total issues = sum of all missing counts (same record can contribute multiple)
        total_issues = (
            missing_enrollment_date +
            missing_cough2weeks +
            missing_poor_weight +
            missing_coughing_blood +
            missing_unexplained_fever +
            missing_night_sweats +
            missing_neck_lymph +
            missing_history_tb +
            missing_date_information_collected +
            missing_tx_previous
        )

        # ── Problematic records for display (limited) ───────────────────────────
        # We use Q to find records with at least one missing field
        has_missing_q = (
            Q(enrollment_date__isnull=True) |
            Q(cough2weeks__isnull=True) |
            Q(poor_weight__isnull=True) |
            Q(coughing_blood__isnull=True) |
            Q(unexplained_fever__isnull=True) |
            Q(night_sweats__isnull=True) |
            Q(neck_lymph__isnull=True) |
            Q(history_tb__isnull=True) |
            Q(date_information_collected__isnull=True) |
            Q(tx_previous__isnull=True)
        )

        problematic_enrollments = enrollments.filter(has_missing_q)[:150]  # safety limit

        missing_records_display = []
        for e in problematic_enrollments:
            missing = []
            if e.enrollment_date is None:
                missing.append("enrollment_date")
            if e.cough2weeks is None:
                missing.append("cough2weeks")
            # ... repeat for all fields (or use a helper list + loop)
            if e.poor_weight is None:
                missing.append("poor_weight")
            if e.coughing_blood is None:
                missing.append("coughing_blood")
            if e.unexplained_fever is None:
                missing.append("unexplained_fever")
            if e.night_sweats is None:
                missing.append("night_sweats")
            if e.neck_lymph is None:
                missing.append("neck_lymph")
            if e.history_tb is None:
                missing.append("history_tb")
            if e.date_information_collected is None:
                missing.append("date_information_collected")
            if e.tx_previous is None:
                missing.append("tx_previous")

            if missing:
                missing_records_display.append({
                    'enrollment_id': e.id,
                    'pid': getattr(e.screening, 'pid', '—'),
                    'site': getattr(getattr(e.screening, 'site', None), 'name', '—'),
                    'enrollment_date': e.enrollment_date,
                    'missing_fields': missing,
                })

        role_context = get_role_context(request.user)

        context = {
            "report_date": timezone.now(),
            "total_enrollments": total_enrollments,
            "total_issues": total_issues,                      # matches context processor logic
            "enrollment_report_total": total_issues,           # for consistency with navbar

            # Individual counts – match keys from context processor
            "missing_enrollment_date": missing_enrollment_date,
            "missing_cough2weeks": missing_cough2weeks,
            "missing_poor_weight": missing_poor_weight,
            "missing_coughing_blood": missing_coughing_blood,
            "missing_unexplained_fever": missing_unexplained_fever,
            "missing_night_sweats": missing_night_sweats,
            "missing_neck_lymph": missing_neck_lymph,
            "missing_history_tb": missing_history_tb,
            "missing_date_information_collected": missing_date_information_collected,
            "missing_tx_previous": missing_tx_previous,

            # Records to display in table/accordion
            "problematic_enrollments": missing_records_display,

            # Role flags
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_site_only": role_context.get("is_site_only", False),
        }

        return render(request, self.template_name, context)