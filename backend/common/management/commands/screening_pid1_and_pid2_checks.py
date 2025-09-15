import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Save rows where pid1 != pid2 with facility names as the first column"

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
            help='Path to output CSV file'
        )

    def handle(self, *args, **options):
        input_csv = options['input']
        output_csv = options['output']

        self.stdout.write(f"Processing input CSV: {input_csv}")

        # Load CSV
        df = pd.read_csv(input_csv)
        df.columns = df.columns.str.strip()  # Clean column names

        # Check required columns
        if 'pid1' not in df.columns or 'pid2' not in df.columns:
            self.stdout.write(self.style.ERROR("CSV must contain 'pid1' and 'pid2' columns"))
            return
        if 'facility_id' not in df.columns:
            self.stdout.write(self.style.ERROR("CSV must contain 'facility_id' column"))
            return

        # Mapping facility_id -> name
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

        # Filter rows where pid1 != pid2
        mismatches = df[df['pid1'] != df['pid2']].copy()

        if mismatches.empty:
            self.stdout.write(self.style.SUCCESS("All rows have matching pid1 and pid2 ✅"))
            return

        # Replace facility_id with name
        mismatches['Site'] = mismatches['facility_id'].map(site_mapping)

        # Put Site name as the first column
        cols = ['Site'] + [c for c in mismatches.columns if c != 'Site']
        mismatches = mismatches[cols]

        # Sort by Site
        mismatches = mismatches.sort_values('Site')

        # Save to CSV
        mismatches.to_csv(output_csv, index=False)
        self.stdout.write(self.style.WARNING(
            f"Found {len(mismatches)} mismatched rows. Saved to {output_csv}"
        ))
