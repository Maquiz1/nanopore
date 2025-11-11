from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context

class ClinicDataQualityReportView(View):
    """
    Clinic Data Quality Report:
    - Checks missing fields individually (sample_received, number_received)
    - Role-based and zone/site filtering
    """

    template_name = "reports/data_quality/laboratory/clinic/data_clinic_quality_report.html"

    def get(self, request, *args, **kwargs):
        Clinic = apps.get_model('nanopore', 'ClinicLaboratory')

        # --- Base QuerySet ---
        clinics = Clinic.objects.select_related(
            'screening',
            'screening__site',
            'screening__site__district__region__zone'
        ).order_by(
            'screening__site__district__region__zone__name',
            'screening__site__name',
            'screening__pid'
        )

        # --- Role-Based Filtering ---
        clinics = filter_queryset_by_user_role(request.user, clinics, site_field="screening__site")

        # --- Optional Filters (Safe) ---
        def safe_int(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return None

        zone_id = safe_int(request.GET.get("zone"))
        site_id = safe_int(request.GET.get("site"))

        if zone_id:
            clinics = clinics.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            clinics = clinics.filter(screening__site_id=site_id)

        total_clinics = clinics.count()

        # --- Helper: serialize for template ---
        def serialize_clinic(c):
            screening = getattr(c, 'screening', None)
            if screening is None:
                return {'pid': '', 'zone_name': '', 'site_name': ''}

            site = getattr(screening, 'site', None)
            district = getattr(site, 'district', None) if site else None
            region = getattr(district, 'region', None) if district else None
            zone = getattr(region, 'zone', None) if region else None

            zone_name = getattr(zone, 'name', '') if zone else ''
            site_name = getattr(site, 'name', '') if site else ''

            return {
                'pid': getattr(screening, 'pid', ''),
                'zone_name': zone_name,
                'site_name': site_name,
            }

        # --- Missing Fields Lists ---
        missing_sample_received = []
        missing_number_received = []

        for c in clinics:
            if getattr(c, 'sample_received', None) in [None, "", False]:
                missing_sample_received.append(serialize_clinic(c))
            if getattr(c, 'number_received', None) in [None, "", False]:
                missing_number_received.append(serialize_clinic(c))

        # --- Role Context ---
        role_context = get_role_context(request.user)

        context = {
            "total_clinics": total_clinics,
            "report_date": timezone.now(),
            "is_admin": role_context.get("is_admin", False),
            "is_zonal_lab": role_context.get("is_zonal_lab", False),
            "is_reviewer": role_context.get("is_reviewer", False),
            "is_site_only": role_context.get("is_site_only", False),
            "is_national_lab": role_context.get("is_national_lab", False),
            "zones": {z.id: z.name for z in role_context.get("zones", [])},
            "sites": {s.id: s.name for s in role_context.get("sites", [])},

            # --- Missing Fields ---
            "missing_sample_received": missing_sample_received,
            "missing_number_received": missing_number_received,
        }

        # --- Total issues count ---
        context["clinic_report_total"] = len(missing_sample_received) + len(missing_number_received)

        return render(request, self.template_name, context)
