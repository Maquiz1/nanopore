import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Find duplicate PIDs in screening CSV and save to a separate CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='Path to input CSV file'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Path to output CSV file for duplicates'
        )

    def handle(self, *args, **options):
        input_csv = options['input']
        output_csv = options['output']

        self.stdout.write(f"Checking duplicates in: {input_csv}")

        # Load CSV
        df = pd.read_csv(input_csv)
        df.columns = df.columns.str.strip()  # clean column names

        # Check if pid column exists
        if 'pid' not in df.columns:
            self.stdout.write(self.style.ERROR("Column 'pid' not found in CSV"))
            return

        # Find duplicates
        duplicates = df[df.duplicated(subset=['pid'], keep=False)]

        if duplicates.empty:
            self.stdout.write(self.style.SUCCESS("No duplicate PIDs found."))
        else:
            # Save duplicates to a separate CSV
            duplicates.to_csv(output_csv, index=False)
            self.stdout.write(self.style.SUCCESS(f"Found {len(duplicates)} duplicate rows. Saved to {output_csv}"))
