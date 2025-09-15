import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Convert clinic laboratory CSV: rename columns, format dates, and convert yes/no fields to integers"

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

        self.stdout.write(f"Converting Clinic Laboratory CSV:\n  Input: {input_csv}\n  Output: {output_csv}")

        # Load CSV (auto-detect delimiter)
        df = pd.read_csv(input_csv, sep=None, engine='python')
        df.columns = df.columns.str.strip()

        # Mapping CSV columns to ClinicLaboratory model fields
        column_mapping = {
            "pid": "PID",
            "lab_name": "TestName",
            # Sputum sample
            "sample_received": "SampleReceived",
            "sample_reason": "SampleReason",
            "other_reason": "OtherReason",
            "new_sample": "NewSample",
            "new_reason": "NewReason",
            "number_received": "NumberReceived",
            # Sputum sample details
            "date_sample1_collected": "DateSample1Collected",
            "date_sample1_received": "DateSample1Received",
            "appearance_sample1": "AppearanceSample1",
            "sample1_volume": "Sample1Volume",
            "date_sample2_collected": "DateSample2Collected",
            "date_sample2_received": "DateSample2Received",
            "appearance_sample2": "AppearanceSample2",
            "sample2_volume": "Sample2Volume",
            # AFB Microscopy
            "afb_microscopy_conducted": "AFBMicroscopyConducted",
            "afb_a_date": "AFBA_Date",
            "technique_a": "TechniqueA",
            "afb_a_results": "AFBAResults",
            "afb_b_date": "AFBB_Date",
            "technique_b": "TechniqueB",
            "afb_b_results": "AFBBResults",
            # Xpert MTB/RIF (Ultra) Test
            "xpert_mtb_rif_conducted": "XpertMTBRifConducted",
            "xpert_date": "XpertDate",
            "xpert_mtb": "XpertMTB",
            "error_code": "ErrorCode",
            "xpert_rif": "XpertRIF",
            "ct_value": "CTValue",
            "ct_na": "CTNA",
            # Additional fields
            "remarks": "Remarks",
        }

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Convert date columns
        date_columns = [
            "DateSample1Received", "DateSample1Collected", "DateSample2Received",
            "DateSample2Collected", "AFBA_Date", "AFBB_Date", "XpertDate"
        ]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')

        # Convert AFBMicroscopyConducted and XpertMTBRifConducted to integers
        yesno_columns = ["AFBMicroscopyConducted", "XpertMTBRifConducted"]
        for col in yesno_columns:
            if col in df.columns:
                # Convert common textual yes/no values to 1/2
                df[col] = df[col].astype(str).str.strip().str.lower()
                df[col] = df[col].replace({
                    "1": 1, "1.0": 1, "yes": 1, "y": 1, "true": 1, "t": 1,
                    "2": 2, "2.0": 2, "no": 2, "n": 2, "false": 2, "f": 2,
                    "none": None, "null": None, "": None
                })
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Keep only columns that exist in ClinicLaboratory model
        upload_columns = list(column_mapping.values())
        df = df[[col for col in upload_columns if col in df.columns]]

        # Save output CSV
        df.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"Clinic Laboratory CSV successfully converted to {output_csv}"))
