# reports/views/exports.py
import csv
from django.http import HttpResponse
from django.views import View
from nanopore.models import Screening


class ScreeningCsvExportView(View):
    """Export all Screening model records to CSV"""

    def get(self, request, *args, **kwargs):
        qs = Screening.objects.select_related("site__district__region__zone", "sex")

        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="screenings.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "PID", 
            # "PID1", "PID2", 
            "Site", "Zone", "Sex",
            "Screening Date", "DOB", "Age", "Eligible",
            "Consent", "Consent Date", "Unable Understand", "Not Willing",
            "Age18Years", "Present Symptoms", "Produce Resp Sample",
            "Genexpert Confirmation", "Enrolled", "Reasons", "Reasons Other", "Remarks"
        ])

        for s in qs:
            writer.writerow([
                s.pid,
                # s.pid1,
                # s.pid2,
                s.site.name if s.site else "",
                s.site.district.region.zone.name if s.site and s.site.district and s.site.district.region and s.site.district.region.zone else "",
                s.sex.name if s.sex else "",
                s.screening_date,
                s.dob,
                s.age,
                s.eligible,
                s.consent.name if s.consent else "",
                s.consent_date,
                s.unable_understand.name if s.unable_understand else "",
                s.not_willing.name if s.not_willing else "",
                s.age18years.name if s.age18years else "",
                s.present_symptoms.name if s.present_symptoms else "",
                s.produce_resp_sample.name if s.produce_resp_sample else "",
                s.genexpert_confirmation.name if s.genexpert_confirmation else "",
                s.enrolled.name if s.enrolled else "",
                s.reasons.name if s.reasons else "",
                s.reasons_other or "",
                s.remarks or "",
            ])

        return response
