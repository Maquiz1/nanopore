import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Save PIDs from a CSV that do NOT have 16 characters"

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
            help='Path to output CSV file for PIDs not having 16 characters'
        )

    def handle(self, *args, **options):
        input_csv = options['input']
        output_csv = options['output']

        self.stdout.write(f"Processing input CSV: {input_csv}")

        # Load CSV
        df = pd.read_csv(input_csv)
        df.columns = df.columns.str.strip()  # Clean column names

        # Check if 'pid' column exists
        if 'pid' not in df.columns:
            self.stdout.write(self.style.ERROR("Column 'pid' not found in CSV"))
            return

        # Filter PIDs NOT having 16 characters
        invalid_pids = df[df['pid'].astype(str).str.len() != 16]

        if invalid_pids.empty:
            self.stdout.write(self.style.SUCCESS("All PIDs have 16 characters. Nothing to save."))
        else:
            invalid_pids.to_csv(output_csv, index=False)
            self.stdout.write(self.style.SUCCESS(
                f"Found {len(invalid_pids)} PIDs NOT having 16 characters. Saved to {output_csv}"
            ))
