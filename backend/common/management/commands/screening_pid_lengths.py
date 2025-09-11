import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Save PIDs NOT having 16 characters with facility names"

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

        if 'pid' not in df.columns:
            self.stdout.write(self.style.ERROR("Column 'pid' not found in CSV"))
            return

        if 'facility_id' not in df.columns:
            self.stdout.write(self.style.ERROR("Column 'facility_id' not found in CSV"))
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

        # Filter PIDs NOT having 16 characters
        invalid_pids = df[df['pid'].astype(str).str.len() != 16].copy()

        # Replace facility_id with name
        invalid_pids['Facility'] = invalid_pids['facility_id'].map(site_mapping)

        # Put facility name as the first column
        cols = ['Facility'] + [c for c in invalid_pids.columns if c != 'Facility']
        invalid_pids = invalid_pids[cols]

        # Sort by facility
        invalid_pids = invalid_pids.sort_values('Facility')

        # Save to CSV
        invalid_pids.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(
            f"Saved {len(invalid_pids)} rows with PIDs NOT having 16 characters to {output_csv}"
        ))
