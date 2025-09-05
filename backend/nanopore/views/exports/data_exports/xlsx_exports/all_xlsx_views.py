import csv
from django.views import View
from django.http import HttpResponse
from openpyxl import Workbook
from nanopore.models import Screening


class AllXlsxDownloadView(View):
    """
    Download Screening + Enrollment combined data as Excel
    """
    def get(self, request, *args, **kwargs):
        wb = Workbook()
        ws = wb.active
        ws.title = "Screening + Enrollment"

        # Header row
        ws.append([
            # Screening fields
            "Zone", "Site", "PID", "Screening Date", "Sex", "DOB", "Age", "Enrolled",
            "Reason", "Other Reason",
            # Enrollment fields
            "Enrollment Date", "Enrollment Remarks"
        ])

        user = request.user
        screenings = Screening.objects.select_related(
            "sex", "site", "enrollment"
        ).all()

        # 🔹 Filter by sites/zones
        if not user.is_superuser:
            allowed_sites = getattr(user, 'sites', None)
            allowed_zones = getattr(user, 'zones', None)
            if allowed_sites:
                screenings = screenings.filter(site__in=allowed_sites.all())
            if allowed_zones:
                screenings = screenings.filter(
                    site__district__region__zone__in=allowed_zones.all()
                )

        for s in screenings:
            e = getattr(s, 'enrollment', None)
            ws.append([
                s.site.district.region.zone.name if s.site and s.site.district and s.site.district.region and s.site.district.region.zone else "",
                s.site.name if s.site else "",
                s.pid,
                s.screening_date,
                s.sex.name if s.sex else "",
                s.dob,
                s.age,
                getattr(s, 'enrolled', ''),
                getattr(s, 'reasons', ''),
                getattr(s, 'reasons_other', ''),
                e.enrollment_date if e else "",
                e.remarks if e else "",
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="screening_enrollment.xlsx"'
        wb.save(response)
        return response
