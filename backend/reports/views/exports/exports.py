import csv
from django.views import View
from django.http import HttpResponse
from openpyxl import Workbook
from nanopore.models import Screening


class AllCsvDownloadView(View):
    """
    Download Screening + Enrollment combined data as CSV
    """
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="screening_enrollment.csv"'

        writer = csv.writer(response)
        writer.writerow([
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
            writer.writerow([
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
        return response

