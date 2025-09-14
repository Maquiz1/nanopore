import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Convert CSV for RegimenChanges: rename columns and clean data"

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

        self.stdout.write(f"Converting RegimenChanges CSV:\n  Input: {input_csv}\n  Output: {output_csv}")

        # Load CSV (auto-detect delimiter)
        df = pd.read_csv(input_csv, sep=None, engine='python')
        df.columns = df.columns.str.strip()

        # Mapping CSV columns to upload-ready field names
        column_mapping = {
            "pid": "PID",
            "date": "Date",
            "drug": "Drug",
            "changes": "Changes",
            "reason": "Reason",
            "specify": "Specify",
        }

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Convert date columns safely to YYYY-MM-DD
        date_columns = ["Date"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')

        # Fill empty fields with empty string
        df = df.fillna("")

        # Keep only relevant columns
        upload_columns = list(column_mapping.values())
        df = df[[col for col in upload_columns if col in df.columns]]

        # Save output CSV
        df.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"RegimenChanges CSV successfully converted to {output_csv}"))
