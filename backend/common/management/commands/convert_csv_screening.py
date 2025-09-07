import pandas as pd
from django.core.management.base import BaseCommand
from datetime import timedelta

class Command(BaseCommand):
    help = "Convert screening CSV from internal format to upload-ready format"

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

        self.stdout.write(f"Converting CSV:\n  Input: {input_csv}\n  Output: {output_csv}")

        # Load CSV
        df = pd.read_csv(input_csv)
        df.columns = df.columns.str.strip()  # remove extra spaces

        # Convert Yes/No fields (1 → Yes, 2 → No)
        yes_no_columns = [
            "present_symptoms",
            "genexpert_confirmation",
            "produce_resp_sample",
            "age18years",
            "consent",
            "not_willing",
            "unable_understand",
            "enrolled",
        ]
        for col in yes_no_columns:
            if col in df.columns:
                df[col] = df[col].map({1: "Yes", 2: "No"}).fillna(df[col])

        # Default 'enrolled' to "Yes" if empty
        if "enrolled" in df.columns:
            df["enrolled"] = df["enrolled"].fillna("Yes")

        # Convert Eligible: 1 -> True, 0 -> False, blanks -> False
        if "eligible" in df.columns:
            df["eligible"] = (
                df["eligible"]
                .astype(str)
                .str.strip()
                .map({"1": True, "0": False, "True": True, "False": False})
                .fillna(False)
            )

        # Convert Sex: 1 -> Male, 2 -> Female
        if "sex" in df.columns:
            df["sex"] = df["sex"].map({1: "Male", 2: "Female"}).fillna(df["sex"])

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

        # Replace Site IDs with names
        site_mapping = {
            1: "Kivunge Hospital",
            2: "Mnazi Mmoja RRH",
            3: "Chunya District Hospital",
            4: "Ziwani Police Hospital",
            5: "Kyela District Hospital",
            6: "Mbeya Zonal RH",
            7: "Mbeya RRH",
            9: "Magu District Hospital",
            10: "Ngudu District Hospital",
            11: "Buzuruga Hospital",
            12: "Sekou Toure RRH",
            13: "Bugando RRH",
            14: "Tambukareli Centre",
            15: "Mbagala Hospital",
            16: "Amana Hospital",
            17: "Mwananyamala Hospital",
            18: "Temeke Hospital",
            19: "Sinza Hospital",
            20: "CTRL Laboratory",
            21: "Unguja PH Laboratory",
            22: "Dodoma RRH",
            23: "Benjamin Mkapa Hospital",
            24: "Mpwapwa District Hospital",
            25: "MAKOLE URBAN HEALTH CENTRE",
        }

        if "Site" in df.columns:
            df["Site"] = df["Site"].map(site_mapping).fillna(df["Site"])

        # Replace Zone IDs with names
        zone_mapping = {
            1: "Dar es salaam",
            2: "Mbeya",
            3: "Mwanza",
            4: "Mbeya",
            5: "Zanzibar",
        }

        if "Zone" in df.columns:
            df["Zone"] = df["Zone"].map(zone_mapping).fillna(df["Zone"])

        # Convert date fields to Django-friendly YYYY-MM-DD
        date_columns = ["ScreeningDate", "DOB", "ConsentDate"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')

        # Calculate missing DOB or Age based on ScreeningDate
        def calculate_dob_age(row):
            try:
                if pd.isna(row["DOB"]) and not pd.isna(row["Age"]):
                    row["DOB"] = (
                        pd.to_datetime(row["ScreeningDate"])
                        - pd.to_timedelta(int(row["Age"]) * 365.25, unit='d')
                    ).strftime('%Y-%m-%d')
                elif pd.isna(row["Age"]) and not pd.isna(row["DOB"]):
                    row["Age"] = int(
                        (pd.to_datetime(row["ScreeningDate"]) - pd.to_datetime(row["DOB"])).days // 365.25
                    )
            except Exception:
                pass
            return row

        df = df.apply(calculate_dob_age, axis=1)

        # Final required upload columns
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

        df = df[upload_columns]

        # Save CSV
        df.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"CSV successfully converted and saved to {output_csv}"))
