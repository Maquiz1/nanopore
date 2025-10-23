from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from django.db.models import Count

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class ScreeningDataQualityReportView(View):
    """
    Screening Data Quality Report:
    - Checks missing fields individually
    - Detects duplicate or invalid PIDs
    - Not eligible participants
    - Role-based and zone/site filtering
    """

    template_name = "reports/data_quality/screenings/data_screening_quality_report.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model('nanopore', 'Screening')

        # --- Base QuerySet ---
        screenings = Screening.objects.select_related(
            'site', 'site__district__region__zone', 'sex',
            'age18years', 'present_symptoms', 'produce_resp_sample',
            'genexpert_confirmation', 'consent', 'unable_understand',
            'not_willing', 'enrolled', 'reasons'
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

        # --- Helper: serialize for template ---
        def serialize_screening(s):
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
                'screening_date': s.screening_date,
                'produce_resp_sample': getattr(s.produce_resp_sample, 'name', None),
                'genexpert_confirmation': getattr(s.genexpert_confirmation, 'name', None),
                'consent': getattr(s.consent, 'name', None),
            }

        # --- Missing Fields (individual lists) ---
        missing_screening_date = []
        missing_pid1 = []
        missing_pid2 = []
        missing_sex = []
        missing_age = []
        missing_dob = []
        missing_consent = []
        missing_age18years = []
        missing_present_symptoms = []
        missing_produce_resp_sample = []
        missing_genexpert_confirmation = []
        missing_unable_understand = []
        missing_not_willing = []
        missing_enrolled = []
        missing_reasons = []

        for s in screenings:
            if not getattr(s, 'screening_date', None):
                missing_screening_date.append(serialize_screening(s))
            if not getattr(s, 'pid1', None):
                missing_pid1.append(serialize_screening(s))
            if not getattr(s, 'pid2', None):
                missing_pid2.append(serialize_screening(s))
                
            if not getattr(s, 'sex', None):
                missing_sex.append(serialize_screening(s))
                
            # Missing Age / DOB
            if not getattr(s, 'age', None) and not getattr(s, 'dob', None):
                # Both missing → flag both
                missing_age.append(serialize_screening(s))
                missing_dob.append(serialize_screening(s))
            elif not getattr(s, 'age', None):
                missing_age.append(serialize_screening(s))
            elif not getattr(s, 'dob', None):
                missing_dob.append(serialize_screening(s))


            if getattr(s, 'consent', None) is None:
                missing_consent.append(serialize_screening(s))
            if getattr(s, 'age18years', None) is None:
                missing_age18years.append(serialize_screening(s))
                
                
            # --- Zone-specific field check ---
            zone_name = getattr(getattr(getattr(getattr(s, 'site', None), 'district', None), 'region', None), 'zone', None)
            zone_name = zone_name.name if zone_name else ''
            
            if zone_name.lower() == "dar es salaam":
                if getattr(s, 'present_symptoms', None) is None:
                    missing_present_symptoms.append(serialize_screening(s))
            else:
                if getattr(s, 'genexpert_confirmation', None) is None:
                    missing_genexpert_confirmation.append(serialize_screening(s))
                               
            if getattr(s, 'produce_resp_sample', None) is None:
                missing_produce_resp_sample.append(serialize_screening(s))
                
            if getattr(s, 'unable_understand', None) is None:
                missing_unable_understand.append(serialize_screening(s))
                
            if getattr(s, 'not_willing', None) is None:
                missing_not_willing.append(serialize_screening(s))
                
            if getattr(s, 'enrolled', None) is None:
                missing_enrolled.append(serialize_screening(s))
                
            if getattr(s, 'reasons', None) is None and getattr(s, 'enrolled', None) and s.enrolled.name.lower() == "no":
                missing_reasons.append(serialize_screening(s))
                
            # Only check missing reasons if enrolled = 96
            # if getattr(s, 'reasons', None) is None and getattr(s, 'enrolled', None) and s.enrolled == 96:
            #     missing_reasons.append(serialize_screening(s))

        # --- PID Issues ---
        duplicate_pids = screenings.values('pid').annotate(pid_count=Count('id')).filter(pid_count__gt=1)
        duplicate_pid_list = [d['pid'] for d in duplicate_pids]
        duplicate_pids_list = [serialize_screening(s) for s in screenings if s.pid in duplicate_pid_list]

        mismatched_pids_list = [serialize_screening(s) for s in screenings if s.pid1 and s.pid2 and s.pid1 != s.pid2]
        invalid_length_pids_list = [serialize_screening(s) for s in screenings if s.pid and len(s.pid) != 16]

        not_eligible_list = [serialize_screening(s) for s in screenings if s.eligible is False]

        # --- Role Context ---
        role_context = get_role_context(request.user)

        context = {
            "total_screenings": total_screenings,
            "report_date": timezone.now(),
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_site_only": role_context.get("is_site_only", False),
            "is_national_lab": role_context.get("is_national_lab", False),
            "zones": {z.id: z.name for z in role_context["zones"]},
            "sites": {s.id: s.name for s in role_context["sites"]},

            # --- Missing Fields ---
            "missing_screening_date": missing_screening_date,
            "missing_pid1": missing_pid1,
            "missing_pid2": missing_pid2,
            "missing_sex": missing_sex,
            "missing_age": missing_age,
            "missing_dob": missing_dob,
            "missing_consent": missing_consent,
            "missing_age18years": missing_age18years,
            "missing_present_symptoms": missing_present_symptoms,
            "missing_produce_resp_sample": missing_produce_resp_sample,
            "missing_genexpert_confirmation": missing_genexpert_confirmation,
            "missing_unable_understand": missing_unable_understand,
            "missing_not_willing": missing_not_willing,
            "missing_enrolled": missing_enrolled,
            "missing_reasons": missing_reasons,

            # --- PID / eligibility issues ---
            "duplicate_pids": duplicate_pids_list,
            "mismatched_pids": mismatched_pids_list,
            "invalid_length_pids": invalid_length_pids_list,
            "not_eligible": not_eligible_list,
        }

        # --- Total issues count ---
        context["screening_report_total"] = (
            len(missing_screening_date) +
            len(missing_pid1) +
            len(missing_pid2) +
            len(missing_sex) +
            len(missing_age) +
            len(missing_dob) +
            len(missing_consent) +
            len(missing_age18years) +
            len(missing_present_symptoms) +
            len(missing_produce_resp_sample) +
            len(missing_genexpert_confirmation) +
            len(missing_unable_understand) +
            len(missing_not_willing) +
            len(missing_enrolled) +
            len(missing_reasons) +
            len(duplicate_pids_list) +
            len(mismatched_pids_list) +
            len(invalid_length_pids_list) +
            len(not_eligible_list)
        )

        return render(request, self.template_name, context)
