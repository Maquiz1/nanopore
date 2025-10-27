import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = (
        "Merge EDCS and TBLIS datasets using unique_lab_no (EDCS) and labno (TBLIS). "
        "Outputs a merged dataset called zonal_edcs_tblis.csv and prints summary stats."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--edcs', '-e',
            type=str,
            required=True,
            help='Path to EDCS CSV file'
        )
        parser.add_argument(
            '--tblis', '-t',
            type=str,
            required=True,
            help='Path to TBLIS CSV file'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Path to output CSV file (merged dataset)'
        )

    def handle(self, *args, **options):
        edcs_csv = options['edcs']
        tblis_csv = options['tblis']
        output_csv = options['output']

        self.stdout.write(f"\n🔄 Merging Datasets:\n  EDCS: {edcs_csv}\n  TBLIS: {tblis_csv}\n")

        # Load CSVs
        edcs_df = pd.read_csv(edcs_csv, sep=None, engine='python')
        tblis_df = pd.read_csv(tblis_csv, sep=None, engine='python')

        # Clean up column names
        edcs_df.columns = edcs_df.columns.str.strip()
        tblis_df.columns = tblis_df.columns.str.strip()

        # Ensure key columns are comparable as strings
        edcs_df["unique_lab_no"] = edcs_df["unique_lab_no"].astype(str).str.strip()
        tblis_df["labno"] = tblis_df["labno"].astype(str).str.strip()

        # --- Merge ---
        merged_df = pd.merge(
            edcs_df,
            tblis_df,
            how='left',
            left_on='unique_lab_no',
            right_on='labno',
            suffixes=('_edcs', '_tblis')
        )

        # --- Keep only specific EDCS columns + all TBLIS columns ---
        edcs_cols = ["pid", "date_sputum_received", "unique_lab_no", "culture_performed"]
        existing_edcs_cols = [col for col in edcs_cols if col in merged_df.columns]
        tblis_cols = [col for col in merged_df.columns if col not in existing_edcs_cols]

        merged_df = merged_df[existing_edcs_cols + tblis_cols]

        # --- Summary Stats ---
        total_records = len(merged_df)
        matched_records = merged_df["labno"].notna().sum() if "labno" in merged_df.columns else 0
        missing_records = total_records - matched_records

        # --- Missing summary (optional) ---
        if "labno" in merged_df.columns:
            missing_summary = merged_df[merged_df['labno'].isna()][["unique_lab_no"]]
            missing_summary.to_csv(output_csv.replace(".csv", "_missing.csv"), index=False)

        # --- Save output ---
        merged_df.to_csv(output_csv, index=False)

        # --- Output summary ---
        self.stdout.write(self.style.SUCCESS("\n✅ Merge Completed Successfully!"))
        self.stdout.write(f"📊 Total records: {total_records}")
        self.stdout.write(f"✅ Matched records: {matched_records}")
        self.stdout.write(f"⚠️ Missing records: {missing_records}")
        self.stdout.write(f"💾 Output saved to: {output_csv}\n")
