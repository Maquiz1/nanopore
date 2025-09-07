import pandas as pd
from django.core.management.base import BaseCommand
from nanopore.models import Screening
from options.models import EnrolledReason  # foreign key model
from datetime import datetime

class Command(BaseCommand):
    help = "Convert PHP MySQL CSV and import into Screening model"

    def add_arguments(self, parser):
        parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='Path to input CSV file (internal PHP/MySQL format)'
        )

    def handle(self, *args, **options):
        input_csv = options['input']
        self.stdout.write(f"Processing CSV: {input_csv}")

        # Load CSV
        df = pd.read_csv(input_csv)
        df.columns = df.columns.str.strip()

        # --- Your existing conversions ---
        yes_no_columns = [
            "present_symptoms","genexpert_confirmation","produce_resp_sample",
            "age18years","consent","not_willing","unable_understand","enrolled",
        ]
        for col in yes_no_columns:
            if col in df.columns:
                df[col] = df[col].map({1:"Yes",2:"No"}).fillna(df[col])
        if "enrolled" in df.columns:
            df["enrolled"] = df["enrolled"].fillna("Yes")
        if "eligible" in df.columns:
            df["eligible"] = df["eligible"].astype(str).str.strip().map({"1":True,"0":False,"True":True,"False":False}).fillna(False)
        if "sex" in df.columns:
            df["sex"] = df["sex"].map({1:"Male",2:"Female"}).fillna(df["sex"])

        # Column mapping
        column_mapping = {
            "pid":"PID", "screening_date":"ScreeningDate","sex":"Sex","dob":"DOB","age":"Age",
            "present_symptoms":"PresentSymptoms","genexpert_confirmation":"GenexpertConfirmation",
            "produce_resp_sample":"ProduceRespSample","age18years":"Age18Years","consent":"Consent",
            "consent_date":"ConsentDate","not_willing":"NotWilling","unable_understand":"UnableUnderstand",
            "enrolled":"Enrolled","reasons":"Reasons","reasons_other":"OtherReason","remarks":"Remarks",
            "eligible":"Eligible","facility_id":"Site","zone":"Zone"
        }
        df = df.rename(columns=column_mapping)

        # Convert date fields
        date_columns = ["ScreeningDate","DOB","ConsentDate"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')

        # Calculate missing DOB or Age
        def calculate_dob_age(row):
            try:
                if pd.isna(row["DOB"]) and not pd.isna(row["Age"]):
                    row["DOB"] = (pd.to_datetime(row["ScreeningDate"]) - pd.to_timedelta(int(row["Age"])*365.25,'d')).strftime('%Y-%m-%d')
                elif pd.isna(row["Age"]) and not pd.isna(row["DOB"]):
                    row["Age"] = int((pd.to_datetime(row["ScreeningDate"]) - pd.to_datetime(row["DOB"])).days // 365.25)
            except:
                pass
            return row
        df = df.apply(calculate_dob_age, axis=1)

        # --- Import into Django ---
        for _, row in df.iterrows():
            # Handle foreign key: reasons
            reasons_obj = None
            if row['Reasons'] and not pd.isna(row['Reasons']):
                try:
                    reasons_obj = EnrolledReason.objects.get(name=row['Reasons'])
                except EnrolledReason.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Reason '{row['Reasons']}' not found. Skipping."))
                    continue

            # Create or update Screening
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
                    'reasons': reasons_obj,
                    'reasons_other': row['OtherReason'],
                    'remarks': row['Remarks'],
                    'eligible': row['Eligible'],
                    'facility_id': row['Site'],
                    'zone': row['Zone'],
                }
            )

        self.stdout.write(self.style.SUCCESS("CSV successfully imported into Screening!"))
