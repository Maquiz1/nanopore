import pandas as pd
from django.core.management.base import BaseCommand
from datetime import timedelta

class Command(BaseCommand):
    help = "Convert enrollment CSV: rename columns and calculate missing DOB/Age"

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

        self.stdout.write(f"Converting Enrollment CSV:\n  Input: {input_csv}\n  Output: {output_csv}")

        # Load CSV
        df = pd.read_csv(input_csv, sep=None, engine='python')  # auto-detect delimiter
        df.columns = df.columns.str.strip()

        # Mapping CSV columns to Enrollment model fields
        column_mapping = {
            "pid": "PID",
            "enrollment_date": "EnrollmentDate",
            
            # Reason(s) for being regarded as presumptive TB patient at initial assessment
            "cough2weeks": "Cough2Weeks",
            "poor_weight": "PoorWeight",
            "coughing_blood": "CoughingBlood",
            "unexplained_fever": "UnexplainedFever",
            "night_sweats": "NightSweats",
            "neck_lymph": "NeckLymph",
            "history_tb": "HistoryTb",
            "date_information_collected": "DateInformationCollected",
            # History of TB and previous treatment
            "tx_previous": "TxPrevious",
            "tb_category": "TbCategory",
            "tb_category_specify": "TbCategorySpecify",
            "tx_month": "TxMonth",
            "tx_unknown_month": "TxUnknownMonth",
            "tx_year": "TxYear",
            "tx_unknown_year": "TxUnknownYear",
            "dr_ds": "DrDs",
            "ltf_months": "LtfMonths",
            "ltf_months_unknown": "LtfMonthsUnknown",
            "tb_regimen": "TbRegimen",
            "tb_regimen_specify": "TbRegimenSpecify",
            "regimen_months": "RegimenMonths",
            "regimen_months_unknown": "RegimenMonthsUnknown",
            "tb_otcome": "TbOutcome",
            # Health-related conditions
            "hiv_status": "HivStatus",
            "other_diseases": "OtherDiseases",
            "diseases_medical": "DiseasesMedical",
            "diseases_specify": "DiseasesSpecify",
            # Samples collections
            "sputum_collected": "SputumCollected",
            "sputum_date": "SputumDate",
            "sputum_reasons": "SputumReasons",
            # ADDITIONAL COLUMNS
            "remarks": "Remarks",
        }

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Convert dates to datetime
        date_columns = ["EnrollmentDate", "DateInformationCollected", "SputumDate"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')


        # Convert dates back to YYYY-MM-DD strings
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].dt.strftime('%Y-%m-%d')

        # Ensure diseases_medical (ManyToMany) is a string list
        if "DiseasesMedical" in df.columns:
            df["DiseasesMedical"] = df["DiseasesMedical"].fillna("").astype(str)

        # Keep only columns that exist in Enrollment model
        upload_columns = list(column_mapping.values())
        df = df[[col for col in upload_columns if col in df.columns]]

        # Save output CSV
        df.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"Enrollment CSV successfully converted to {output_csv}"))
