import pandas as pd
from django.core.management.base import BaseCommand
from nanopore.models import Screening
from datetime import datetime

class Command(BaseCommand):
    help = "Import screening data from CSV to PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv', '-c',
            type=str,
            required=True,
            help='Path to the converted upload-ready CSV'
        )

    def handle(self, *args, **options):
        csv_file = options['csv']
        self.stdout.write(f"Importing data from {csv_file}...")

        df = pd.read_csv(csv_file)
        for _, row in df.iterrows():
            # Create or update Screening object
            Screening.objects.update_or_create(
                pid=row['PID'],
                defaults={
                    'screening_date': row['ScreeningDate'] if row['ScreeningDate'] else None,
                    'sex': row['Sex'],
                    'dob': row['DOB'] if row['DOB'] else None,
                    'age': row['Age'],
                    'present_symptoms': row['PresentSymptoms'],
                    'genexpert_confirmation': row['GenexpertConfirmation'],
                    'produce_resp_sample': row['ProduceRespSample'],
                    'age18years': row['Age18Years'],
                    'consent': row['Consent'],
                    'consent_date': row['ConsentDate'] if row['ConsentDate'] else None,
                    'not_willing': row['NotWilling'],
                    'unable_understand': row['UnableUnderstand'],
                    'enrolled': row['Enrolled'],
                    'reasons': row['Reasons'],
                    'reasons_other': row['OtherReason'],
                    'remarks': row['Remarks'],
                    'eligible': row['Eligible'],
                    'facility_id': row['Site'],
                    'zone': row['Zone'],
                }
            )

        self.stdout.write(self.style.SUCCESS("Data imported successfully!"))
