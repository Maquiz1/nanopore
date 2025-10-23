from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Count

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class ScreeningDataQualityReportView(View):
    """Data Quality Report for Screening model:
    - Checks missing fields
    - Detects duplicate or invalid PIDs
    - Role-based and zone/site filtering
    """

    template_name = "reports/data_quality/screening/data_screening_quality_report.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model('nanopore', 'Screening')

        # --- Base QuerySet ---
        screenings = Screening.objects.select_related(
            'site',
            'site__district__region__zone',
            'sex',
            'age18years',
            'present_symptoms',
            'produce_resp_sample',
            'genexpert_confirmation',
            'consent',
            'unable_understand',
            'not_willing',
            'enrolled',
        ).order_by(
            'site__district__region__zone__name',
            'site__name',
            'pid'
        )

        # --- Role-Based Filtering ---
        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        # --- Optional Filters ---
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        if zone_id:
            screenings = screenings.filter(site__district__region__zone_id=zone_id)
        if site_id:
            screenings = screenings.filter(site_id=site_id)

        total_screenings = screenings.count()

        # --- Helper: Serialize Screening ---
        def serialize_screening(s, extra_info=None):
            zone_name = getattr(getattr(getattr(getattr(s, 'site', None), 'district', None), 'region', None), 'zone', None)
            zone_name = zone_name.name if zone_name else ''
            site_name = getattr(getattr(s, 'site', None), 'name', '')
            sex_name = getattr(getattr(s, 'sex', None), 'name', '')

            return {
                'pid': s.pid,
                'pid1': s.pid1,
                'pid2': s.pid2,
                'zone_name': zone_name,
                'site_name': site_name,
                'sex': sex_name,
                'age': s.age,
                'dob': s.dob,
                'eligible': s.eligible,
                'missing_fields': extra_info.get("missing_fields") if extra_info else [],
                'issue': extra_info.get("issue") if extra_info else None,
                'screening_date': s.screening_date,
                'created_at': s.created_at,
            }

        # --- 1️⃣ Missing Fields Check ---
        missing_fields_records = []
        for s in screenings:
            missing_fields = []
            required_fields = {
                "pid1": s.pid1,
                "pid2": s.pid2,
                "sex": s.sex,
                "site": s.site,
                "screening_date": s.screening_date,
                "age_or_dob": s.age or s.dob,
                "consent": s.consent,
            }
            for field_name, value in required_fields.items():
                if not value:
                    missing_fields.append(field_name)

            if missing_fields:
                missing_fields_records.append(serialize_screening(s, {"missing_fields": missing_fields}))

        # --- 2️⃣ PID Issues ---
        pid_issues = []

        # Duplicate PIDs
        duplicate_pids = (
            screenings.values('pid')
            .annotate(pid_count=Count('id'))
            .filter(pid_count__gt=1)
        )
        duplicate_pid_list = [d['pid'] for d in duplicate_pids]

        for s in screenings:
            if s.pid in duplicate_pid_list:
                pid_issues.append(serialize_screening(s, {"issue": "Duplicate PID"}))
            elif s.pid1 and s.pid2 and s.pid1 != s.pid2:
                pid_issues.append(serialize_screening(s, {"issue": "PID1 not equal to PID2"}))
            elif s.pid and len(s.pid) != 16:
                pid_issues.append(serialize_screening(s, {"issue": "PID length not 16 characters"}))

        # --- 3️⃣ Not Eligible ---
        not_eligible = screenings.filter(eligible=False)

        # --- Role Context ---
        role_context = get_role_context(request.user)
        is_admin = role_context.get("is_admin", False)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_reviewer = role_context.get("is_reviewer", False)
        is_site_only = role_context.get("is_site_only", False)
        is_national_lab = role_context.get("is_national_lab", False)

        # --- Context for Template ---
        context = {
            "total_screenings": total_screenings,
            "not_eligible": [serialize_screening(s) for s in not_eligible],
            "missing_fields_records": missing_fields_records,
            "pid_issues": pid_issues,
            "report_date": timezone.now(),
            "is_admin": is_admin,
            "is_zonal_lab": is_zonal_lab,
            "is_reviewer": is_reviewer,
            "is_site_only": is_site_only,
            "is_national_lab": is_national_lab,
            "zones": {z.id: z.name for z in role_context["zones"]},
            "sites": {s.id: s.name for s in role_context["sites"]},
        }

        # --- Totals ---
        context["screening_report_total"] = (
            len(context["not_eligible"])
            + len(context["missing_fields_records"])
            + len(context["pid_issues"])
        )

        return render(request, self.template_name, context)
