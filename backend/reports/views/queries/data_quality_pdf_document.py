from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.apps import apps
import weasyprint

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class DreamFundQueriesPDFView(View):
    """Generate DREAM FUND - NANOPORE TB SEQUENCING QUERIES REPORT PDF with user info."""

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model('nanopore', 'Screening')

        screenings = Screening.objects.select_related(
            'site', 'site__district', 'site__district__region', 'site__district__region__zone',
            'clinic_laboratory', 'diagnosis', 'zonal_laboratory'
        ).order_by('site__district__region__zone__name', 'site__name', 'pid')

        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        role_context = get_role_context(request.user)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_admin = role_context.get("is_admin", False)
        is_reviewer = role_context.get("is_reviewer", False)
        is_superuser = request.user.is_superuser

        def serialize_screening(s):
            zone_name = getattr(getattr(getattr(getattr(s, 'site', None), 'district', None), 'region', None), 'zone', None)
            zone_name = zone_name.name if zone_name else ''
            return {
                'pid': getattr(s, 'pid', ''),
                'zone_name': zone_name,
                'site_name': getattr(getattr(s, 'site', None), 'name', ''),
                'clinic_lab_name': getattr(getattr(s, 'clinic_laboratory', None), 'name', ''),
                'zonal_lab_name': getattr(getattr(s, 'zonal_laboratory', None), 'name', ''),
                'diagnosis_name': getattr(getattr(s, 'diagnosis', None), 'name', ''),
                'regimen_changed': getattr(getattr(s, 'diagnosis', None), 'regimen_changed', False),
                'regimen_missing': not getattr(s, 'regimen_changes', None) or not s.regimen_changes.exists() if getattr(getattr(s, 'diagnosis', None), 'regimen_changed', False) else False,
                'tb_treatment_date': getattr(getattr(s, 'diagnosis', None), 'tb_treatment_date', None),
                'tb_outcome2': getattr(getattr(s, 'diagnosis', None), 'tb_outcome2', ''),
                'tb_outcome2_date': getattr(getattr(s, 'diagnosis', None), 'tb_outcome2_date', ''),
                'xpert_mtb': getattr(getattr(s, 'clinic_laboratory', None), 'xpert_mtb', ''),
                'months_since_treatment': (timezone.now().date() - getattr(getattr(s, 'diagnosis', None), 'tb_treatment_date', timezone.now().date())).days // 30 if getattr(getattr(s, 'diagnosis', None), 'tb_treatment_date', None) else None
            }

        seven_months_ago = timezone.now().date() - timedelta(days=210)
        treatment_started_7m_ago = screenings.filter(
            diagnosis__tb_treatment=1,
            diagnosis__tb_treatment_date__isnull=False,
            diagnosis__tb_treatment_date__lte=seven_months_ago
        )
        pending_tb_outcomes = treatment_started_7m_ago.filter(diagnosis__tb_outcome2__isnull=True)
        pending_tb_outcomes_date = treatment_started_7m_ago.filter(diagnosis__tb_outcome2_date__isnull=True)

        # --- Context ---
        context = {
            "total_screenings": screenings.count(),
            "download_date": timezone.now(),
            "downloaded_by": request.user.get_full_name() or request.user.username,
            "user_prefix": getattr(getattr(request.user, "profile", None), "prefix", ""),
            "user_position": getattr(getattr(request.user, "profile", None), "position", ""),
            "user_zone": getattr(getattr(getattr(getattr(request.user, 'profile', None), 'site', None), 'district', None), 'region', None).zone.name if getattr(request.user, 'profile', None) and getattr(request.user.profile, 'site', None) else "",
            "user_site": getattr(getattr(request.user, 'profile', None), 'site', None).name if getattr(request.user, 'profile', None) and getattr(request.user.profile, 'site', None) else "",
        }

        # --- Substudy2 & other sections ---
        if is_zonal_lab or is_admin or is_superuser or is_reviewer:
            context["enrolled_substudy2_missing_zonal_lab"] = [
                serialize_screening(s) for s in screenings.filter(
                    clinic_laboratory__xpert_mtb_rif_conducted=1,
                    clinic_laboratory__xpert_mtb__in=[2,3,4,5,6],
                    zonal_laboratory__isnull=True
                )
            ]
        else:
            context["enrolled_substudy2_missing_zonal_lab"] = []

        if is_zonal_lab and not (is_admin or is_superuser):
            for key in ["not_eligible","eligible_not_enrolled","enrolled_missing_clinic_laboratory_data","enrolled_missing_diagnosis_data","diagnosis_regimen_changed_missing_regimen","pending_outcomes","pending_outcomes_date"]:
                context.pop(key, None)
        else:
            context.update({
                "not_eligible": [serialize_screening(s) for s in screenings.filter(eligible=False)],
                "eligible_not_enrolled": [serialize_screening(s) for s in screenings.filter(eligible=True, enrollment__isnull=True)],
                "enrolled_missing_clinic_laboratory_data": [serialize_screening(s) for s in screenings.filter(eligible=True, clinic_laboratory__isnull=True)],
                "enrolled_missing_diagnosis_data": [serialize_screening(s) for s in screenings.filter(eligible=True, diagnosis__isnull=True)],
                "diagnosis_regimen_changed_missing_regimen": [serialize_screening(s) for s in screenings.filter(eligible=True, diagnosis__regimen_changed=True).filter(~Q(regimen_changes__isnull=False)).distinct()],
                "pending_outcomes": [serialize_screening(s) for s in pending_tb_outcomes],
                "pending_outcomes_date": [serialize_screening(s) for s in pending_tb_outcomes_date],
            })

        visible_sections = [k for k,v in context.items() if isinstance(v,list) and k!="not_eligible"]
        context["report_total"] = sum(len(context[k]) for k in visible_sections)

        html_string = render_to_string(
            'reports/data_quality/dreamfund_queries_report.html',
            context,
            request=request
        )
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="dreamfund_queries_report.pdf"'
        weasyprint.HTML(string=html_string).write_pdf(response)
        return response
