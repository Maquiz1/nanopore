import csv
from django.views import View
from django.http import HttpResponse
from nanopore.models import Screening

class ScreeningCsvDownloadView(View):
    """
    Download screening records as CSV, filtered by the user's allowed sites or zones.
    """
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="screenings.csv"'

        writer = csv.writer(response)

        # CSV Header
        writer.writerow([
            'PID', 'Screening Date', 'Sex', 'DOB', 'Age', 'Present Symptoms',
            'Genexpert Confirmation', 'Produce Respiratory Sample', 'Age >=18',
            'Consent', 'Consent Date', 'Not Willing', 'Unable to Understand',
            'Enrolled', 'Reason', 'Other Reason', 'Remarks', 'Eligible', 'Site', 'Zone'
        ])

        user = request.user

        screenings = Screening.objects.all()

        # Optional filtering by allowed sites/zones if user has these attributes
        if hasattr(user, 'sites') and user.sites.exists():
            screenings = screenings.filter(site__in=user.sites.all())

        if hasattr(user, 'zones') and user.zones.exists():
            screenings = screenings.filter(site__district__region__zone__in=user.zones.all())

        if user.is_superuser:
            screenings = Screening.objects.all()  # Superuser sees all

        screenings = screenings.order_by('screening_date')

        for s in screenings:
            # Safely get zone name
            zone_name = ""
            if s.site and s.site.district and s.site.district.region and s.site.district.region.zone:
                zone_name = s.site.district.region.zone.name

            writer.writerow([
                s.pid,
                s.screening_date,
                s.sex.name if s.sex else '',
                s.dob,
                s.age,
                s.present_symptoms.name if s.present_symptoms else '',
                s.genexpert_confirmation.name if s.genexpert_confirmation else '',
                s.produce_resp_sample.name if s.produce_resp_sample else '',
                s.age18years.name if s.age18years else '',
                s.consent.name if s.consent else '',
                s.consent_date,
                s.not_willing.name if s.not_willing else '',
                s.unable_understand.name if s.unable_understand else '',
                s.enrolled.name if s.enrolled else '',
                s.reasons.name if s.reasons else '',
                s.reasons_other or '',
                s.remarks or '',
                s.eligible,
                s.site.name if s.site else '',
                zone_name,
            ])

        return response
