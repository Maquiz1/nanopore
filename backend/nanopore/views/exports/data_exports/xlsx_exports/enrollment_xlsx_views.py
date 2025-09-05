import csv
from django.views import View
from django.http import HttpResponse
from openpyxl import Workbook
from nanopore.models import Enrollment


# ---------------- X Export ----------------
class EnrollmentXlsxDownloadView(View):
    """
    Download Enrollment records as XLSX.
    """
    def get(self, request, *args, **kwargs):
        wb = Workbook()
        ws = wb.active
        ws.title = "Enrollments"

        # Header row
        ws.append([
            "PID", "Screening Date", "Sex", "DOB", "Age", "Enrolled",
            "Enrollment Date", "Reason", "Other Reason", "Remarks", "Site", "Zone"
        ])

        user = request.user
        enrollments = Enrollment.objects.select_related('screening').all()

        # Filter based on allowed sites/zones if user is not superuser
        if not user.is_superuser:
            allowed_sites = getattr(user, 'sites', None)
            allowed_zones = getattr(user, 'zones', None)
            if allowed_sites:
                enrollments = enrollments.filter(screening__site__in=allowed_sites.all())
            if allowed_zones:
                enrollments = enrollments.filter(
                    screening__site__district__region__zone__in=allowed_zones.all()
                )

        # Populate Excel rows
        for e in enrollments:
            s = e.screening
            ws.append([
                s.pid if s else "",
                s.screening_date if s else "",
                s.sex.name if s and s.sex else "",
                s.dob if s else "",
                s.age if s else "",
                getattr(s, 'enrolled', ''),
                e.enrollment_date,
                getattr(s, 'reasons', ''),
                getattr(s, 'reasons_other', ''),
                e.remarks or "",
                s.site.name if s and s.site else "",
                s.site.district.region.zone.name if s and s.site and s.site.district and s.site.district.region and s.site.district.region.zone else ""
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="enrollments.xlsx"'
        wb.save(response)
        return response
