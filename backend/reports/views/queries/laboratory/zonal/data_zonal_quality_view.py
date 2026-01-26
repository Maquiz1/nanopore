from django.views import View
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.apps import apps

from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


class ZonalDataQualityReportView(View):
    """Generate categorized data quality report for screenings and related models (role-aware)."""

    template_name = "reports/data_quality/laboratory/zonal/data_zonal_quality_report.html"

    def get(self, request, *args, **kwargs):
        Screening = apps.get_model('nanopore', 'Screening')

        # --- Base QuerySet ---
        screenings = Screening.objects.select_related(
            'site',
            'site__district__region__zone',
            'clinic_laboratory',
            'diagnosis',
            'zonal_laboratory'
        ).order_by(
            'site__district__region__zone__name',
            'site__name',
            'pid'
        )

        # --- Role-Based Filtering ---
        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

        # Optional filters via GET
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        if zone_id:
            screenings = screenings.filter(site__district__region__zone_id=zone_id)
        if site_id:
            screenings = screenings.filter(site_id=site_id)

        total_screenings = screenings.count()

        # --- Helper: Convert screening to dict ---
        def serialize_screening(s):
            zone_name = getattr(getattr(getattr(getattr(s, 'site', None), 'district', None), 'region', None), 'zone', None)
            zone_name = zone_name.name if zone_name else ''
            site_name = getattr(getattr(s, 'site', None), 'name', '')

            clinic_lab_name = getattr(getattr(s, 'clinic_laboratory', None), 'name', '')
            zonal_lab_name = getattr(getattr(s, 'zonal_laboratory', None), 'name', '')
            diagnosis_name = getattr(getattr(s, 'diagnosis', None), 'name', '')

            missing_fields = []
            if not clinic_lab_name:
                missing_fields.append("Clinic")
            if not diagnosis_name:
                missing_fields.append("Diagnosis")

            regimen_missing = False
            if getattr(s, 'diagnosis', None) and getattr(s.diagnosis, 'regimen_changed', False):
                if not getattr(s, 'regimen_changes', None) or not s.regimen_changes.exists():
                    regimen_missing = True

            tb_treatment_date = getattr(getattr(s, 'diagnosis', None), 'tb_treatment_date', None)
            tb_outcome2 = getattr(getattr(s, 'diagnosis', None), 'tb_outcome2', '')
            regimen_changed = getattr(getattr(s, 'diagnosis', None), 'regimen_changed', '')

            months_since_treatment = None
            if tb_treatment_date:
                delta = timezone.now().date() - tb_treatment_date
                months_since_treatment = delta.days // 30

            xpert_mtb = getattr(getattr(s, 'clinic_laboratory', None), 'xpert_mtb', '')

            return {
                'pid': getattr(s, 'pid', ''),
                'zone_name': zone_name,
                'site_name': site_name,
                'clinic_lab_name': clinic_lab_name,
                'zonal_lab_name': zonal_lab_name,
                'diagnosis_name': diagnosis_name,
                'missing_fields': missing_fields,
                'regimen_missing': regimen_missing,
                'tb_treatment_date': tb_treatment_date,
                'tb_outcome2': tb_outcome2,
                'months_since_treatment': months_since_treatment,
                'regimen_changed': regimen_changed,
                'xpert_mtb': xpert_mtb,
            }

        # --- Filters ---
        six_months_ago = timezone.now().date() - timedelta(days=180)
        treatment_started_6m_ago = screenings.filter(
            diagnosis__tb_treatment=1,
            diagnosis__tb_treatment_date__isnull=False,
            diagnosis__tb_treatment_date__lte=six_months_ago
        )
        pending_tb_outcomes = treatment_started_6m_ago.filter(Q(diagnosis__tb_outcome2__isnull=True))
        pending_tb_outcomes_date = treatment_started_6m_ago.filter(Q(diagnosis__tb_outcome2_date__isnull=True))

        # --- Role Context ---
        role_context = get_role_context(request.user)
        is_zonal_lab = role_context.get("is_zonal_lab", False)
        is_admin = role_context.get("is_admin", False)
        is_reviewer = role_context.get("is_reviewer", False)

        # --- Context Data ---
        context = {"total_screenings": total_screenings}

        # --- Substudy2 Missing Zonal Lab (for superuser/admin/reviewer/zonal lab) ---
        if request.user.is_superuser or is_admin or is_reviewer or is_zonal_lab:
            context["enrolled_substudy2_missing_zonal_lab"] = [
                serialize_screening(s) for s in screenings.filter(
                    clinic_laboratory__xpert_mtb_rif_conducted=1,
                    clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
                    zonal_laboratory__isnull=True
                )
            ]
        else:
            context["enrolled_substudy2_missing_zonal_lab"] = []

        # --- Other sections ---
        if is_zonal_lab and not (is_admin or request.user.is_superuser):
            # Zonal lab only sees Substudy2
            for key in [
                "not_eligible",
                "eligible_not_enrolled",
                "enrolled_missing_clinic_laboratory_data",
                "enrolled_missing_diagnosis_data",
                "diagnosis_regimen_changed_missing_regimen",
                "pending_outcomes",
                "pending_outcomes_date",
            ]:
                context.pop(key, None)
        else:
            # Normal users see all sections
            context.update({
                "not_eligible": [serialize_screening(s) for s in screenings.filter(eligible=False)],
                "eligible_not_enrolled": [serialize_screening(s) for s in screenings.filter(eligible=True, enrollment__isnull=True)],
                "enrolled_missing_clinic_laboratory_data": [serialize_screening(s) for s in screenings.filter(eligible=True, clinic_laboratory__isnull=True)],
                "enrolled_missing_diagnosis_data": [serialize_screening(s) for s in screenings.filter(eligible=True, diagnosis__isnull=True)],
                "diagnosis_regimen_changed_missing_regimen": [serialize_screening(s) for s in screenings.filter(
                    eligible=True, diagnosis__regimen_changed=True).filter(~Q(regimen_changes__isnull=False)).distinct()],
                "pending_outcomes": [serialize_screening(s) for s in pending_tb_outcomes],
                "pending_outcomes_date": [serialize_screening(s) for s in pending_tb_outcomes_date],
            })

        # --- Recalculate report_total for visible sections only ---
        report_total = sum(
            len(v) for k, v in context.items() if isinstance(v, list) and k != "not_eligible"
        )
        context["report_total"] = report_total

        # --- Add months_since_treatment ---
        for group in ["pending_outcomes", "pending_outcomes_date"]:
            for s in context.get(group, []):
                if s['tb_treatment_date']:
                    delta = timezone.now().date() - s['tb_treatment_date']
                    s['months_since_treatment'] = delta.days // 30

        # --- Add role flags for template ---
        context.update({
            "is_admin": is_admin,
            "is_zonal_lab": is_zonal_lab,
            "is_national_lab": role_context.get("is_national_lab", False),
            "is_site_only": role_context.get("is_site_only", False),
            "zones": {z.id: z.name for z in role_context["zones"]},
            "sites": {s.id: s.name for s in role_context["sites"]},
        })
        
        context.update({
            "report_date": timezone.now(),
        })

        return render(request, self.template_name, context)
