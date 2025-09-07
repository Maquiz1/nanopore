import pandas as pd
from django.core.management.base import BaseCommand
from datetime import timedelta

class Command(BaseCommand):
    help = "Convert screening CSV: rename columns and calculate missing DOB/Age"

    def add_arguments(self, parser):
        parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='Path to input CSV file (internal format)'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Path to output CSV file (upload-ready format)'
        )

    def handle(self, *args, **options):
        input_csv = options['input']
        output_csv = options['output']

        self.stdout.write(f"Renaming columns and calculating DOB/Age:\n  Input: {input_csv}\n  Output: {output_csv}")

        # Load CSV
        df = pd.read_csv(input_csv)
        df.columns = df.columns.str.strip()  # remove extra spaces

        # Mapping columns from internal/download to upload-ready
        column_mapping = {
            "pid": "PID",
            "screening_date": "ScreeningDate",
            "sex": "Sex",
            "dob": "DOB",
            "age": "Age",
            "present_symptoms": "PresentSymptoms",
            "genexpert_confirmation": "GenexpertConfirmation",
            "produce_resp_sample": "ProduceRespSample",
            "age18years": "Age18Years",
            "consent": "Consent",
            "consent_date": "ConsentDate",
            "not_willing": "NotWilling",
            "unable_understand": "UnableUnderstand",
            "enrolled": "Enrolled",
            "reasons": "Reasons",
            "reasons_other": "OtherReason",
            "remarks": "Remarks",
            "eligible": "Eligible",
            "facility_id": "Site",
            "zone": "Zone"
        }

        df = df.rename(columns=column_mapping)

        # Convert dates to datetime to allow calculations
        df['ScreeningDate'] = pd.to_datetime(df['ScreeningDate'], errors='coerce')
        df['DOB'] = pd.to_datetime(df['DOB'], errors='coerce')

        # Calculate missing DOB or Age
        def calculate_dob_age(row):
            screening_date = row.get("ScreeningDate")
            dob = row.get("DOB")
            age = row.get("Age")

            # If ScreeningDate is missing, do nothing
            if pd.isna(screening_date):
                return row

            # Calculate missing DOB if Age exists
            if pd.isna(dob) and pd.notna(age):
                try:
                    row["DOB"] = screening_date - timedelta(days=int(age) * 365)
                except Exception:
                    pass

            # Calculate missing Age if DOB exists
            elif pd.isna(age) and pd.notna(dob):
                try:
                    row["Age"] = (screening_date - dob).days // 365
                except Exception:
                    pass

            return row

        df = df.apply(calculate_dob_age, axis=1)

        # Convert dates back to string YYYY-MM-DD
        df['ScreeningDate'] = df['ScreeningDate'].dt.strftime('%Y-%m-%d')
        df['DOB'] = df['DOB'].dt.strftime('%Y-%m-%d')

        # Keep only the expected upload columns
        upload_columns = [
            "PID",
            "ScreeningDate",
            "Sex",
            "DOB",
            "Age",
            "PresentSymptoms",
            "GenexpertConfirmation",
            "ProduceRespSample",
            "Age18Years",
            "Consent",
            "ConsentDate",
            "NotWilling",
            "UnableUnderstand",
            "Enrolled",
            "Reasons",
            "OtherReason",
            "Remarks",
            "Eligible",
            "Site",
            "Zone"
        ]
        # df = df[upload_columns]
        
        # Convert Eligible to Boolean
        # if "Eligible" in df.columns:
        #     df["Eligible"] = df["Eligible"].astype(str).str.strip().map({
        #         "1": True,
        #         "0": False,
        #         "True": True,
        #         "False": False
        #     }).fillna(False)  # default False if missing or invalid
            
        # --- Convert Eligible to proper boolean ---
        if "Eligible" in df.columns:
            def to_bool(val):
                if pd.isna(val):
                    return False
                val_str = str(val).strip().lower()
                if val_str in ["1", "true", "yes"]:
                    return True
                elif val_str in ["0", "false", "no"]:
                    return False
                return False  # default

        df["Eligible"] = df["Eligible"].apply(to_bool).astype(bool)

        # Keep only the expected upload columns
        df = df[upload_columns]

        # Save CSV
        df.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"CSV successfully renamed and saved to {output_csv}"))
