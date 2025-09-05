import csv
from django.http import HttpResponse
from django.views import View
from nanopore.models import Screening

class ScreeningCsvTemplateDownloadView(View):
    """
    Provides a CSV template for uploading Screening records,
    matching the structure of the downloaded screening data.
    """
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="screening_upload_template.csv"'

        writer = csv.writer(response)

        # Match the headers from ScreeningCsvDownloadView
        # headers = [
        #     'PID', 'Screening Date', 'Sex', 'DOB', 'Age', 'Present Symptoms',
        #     'Genexpert Confirmation', 'Produce Respiratory Sample', 'Age >=18',
        #     'Consent', 'Consent Date', 'Not Willing', 'Unable to Understand',
        #     'Enrolled', 'Reason', 'Other Reason', 'Remarks', 'Eligible', 'Site', 'Zone'
        # ]
        
        headers = [
            'PID', 'ScreeningDate', 'Sex', 'DOB', 'Age', 'PresentSymptoms',
            'GenexpertConfirmation', 'ProduceRespSample', 'Age18Years',
            'Consent', 'ConsentDate', 'NotWilling', 'UnableUnderstand',
            'Enrolled', 'Reasons', 'OtherReason', 'Remarks', 'Eligible', 'Site', 'Zone'
        ]
        writer.writerow(headers)

        # Optional: Add a sample row using the first existing Screening if available
        sample = Screening.objects.first()
        if sample:
            zone_name = ""
            if sample.site and sample.site.district and sample.site.district.region and sample.site.district.region.zone:
                zone_name = sample.site.district.region.zone.name

            sample_row = [
                sample.pid,
                sample.screening_date,
                sample.sex.name if sample.sex else '',
                sample.dob,
                sample.age,
                sample.present_symptoms.name if sample.present_symptoms else '',
                sample.genexpert_confirmation.name if sample.genexpert_confirmation else '',
                sample.produce_resp_sample.name if sample.produce_resp_sample else '',
                sample.age18years.name if sample.age18years else '',
                sample.consent.name if sample.consent else '',
                sample.consent_date,
                sample.not_willing.name if sample.not_willing else '',
                sample.unable_understand.name if sample.unable_understand else '',
                sample.enrolled.name if sample.enrolled else '',
                sample.reasons.name if sample.reasons else '',
                sample.reasons_other or '',
                sample.remarks or '',
                sample.eligible,
                sample.site.name if sample.site else '',
                zone_name,
            ]
            writer.writerow(sample_row)
        else:
            # Empty row example
            writer.writerow([''] * len(headers))

        return response
