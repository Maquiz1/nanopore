import pandas as pd
from django.core.management.base import BaseCommand
from datetime import datetime
import os

class Command(BaseCommand):
    help = (
        "Merge EDCS and TBLIS datasets using unique_lab_no (EDCS left) "
        "and labno (TBLIS right). Saves merged, missing, and appendable summary CSV files."
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
            help='Path to output merged CSV file'
        )

    def handle(self, *args, **options):
        edcs_csv = options['edcs']
        tblis_csv = options['tblis']
        output_csv = options['output']

        self.stdout.write(f"🔄 Starting merge process:\n  🧾 EDCS: {edcs_csv}\n  🧬 TBLIS: {tblis_csv}\n  💾 Output: {output_csv}")

        # --- Load datasets ---
        edcs_df = pd.read_csv(edcs_csv, sep=None, engine='python')
        tblis_df = pd.read_csv(tblis_csv, sep=None, engine='python')

        edcs_df.columns = edcs_df.columns.str.strip()
        tblis_df.columns = tblis_df.columns.str.strip()

        # --- Validate required columns ---
        if 'unique_lab_no' not in edcs_df.columns:
            raise KeyError("❌ 'unique_lab_no' column not found in EDCS dataset.")
        if 'labno' not in tblis_df.columns:
            raise KeyError("❌ 'labno' column not found in TBLIS dataset.")

        # --- Normalize join keys ---
        edcs_df['unique_lab_no'] = edcs_df['unique_lab_no'].astype(str).str.strip()
        tblis_df['labno'] = tblis_df['labno'].astype(str).str.strip()

        # --- Merge datasets ---
        merged_df = pd.merge(
            edcs_df,
            tblis_df,
            how='left',
            left_on='unique_lab_no',
            right_on='labno',
            suffixes=('_edcs', '_tblis')
        )

        # --- Identify labno column after merge ---
        labno_col = None
        for col in merged_df.columns:
            if col.lower() in ['labno', 'labno_tblis']:
                labno_col = col
                break

        if not labno_col:
            self.stdout.write(self.style.WARNING("⚠️ Could not find 'labno' column after merge — skipping summary."))
            merged_df.to_csv(output_csv, index=False)
            return

        # --- Summary calculations ---
        total_edcs = len(edcs_df)
        total_tblis = len(tblis_df)
        missing_df = merged_df[merged_df[labno_col].isna()][['unique_lab_no']]
        total_missing = len(missing_df)
        total_matched = total_edcs - total_missing
        match_percentage = round((total_matched / total_edcs) * 100, 2) if total_edcs > 0 else 0.0

        # --- Save merged dataset ---
        merged_df.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"✅ Merged dataset saved to: {output_csv}"))

        # --- Save missing dataset ---
        if total_missing > 0:
            missing_file = output_csv.replace('.csv', '_missing.csv')
            missing_df.to_csv(missing_file, index=False)
            self.stdout.write(
                self.style.WARNING(f"⚠️ {total_missing} unmatched records saved to: {missing_file}")
            )

        # --- Appendable summary file ---
        summary_file = output_csv.replace('.csv', '_summary.csv')
        summary_data = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "EDCS_File": os.path.basename(edcs_csv),
            "TBLIS_File": os.path.basename(tblis_csv),
            "Merged_File": os.path.basename(output_csv),
            "Total_EDCS_Records": total_edcs,
            "Total_TBLIS_Records": total_tblis,
            "Matched_Records": total_matched,
            "Unmatched_Records": total_missing,
            "Match_Percentage": match_percentage
        }

        # --- Append or create summary ---
        if os.path.exists(summary_file):
            pd.DataFrame([summary_data]).to_csv(summary_file, mode='a', header=False, index=False)
            self.stdout.write(self.style.SUCCESS(f"📈 Summary appended to: {summary_file}"))
        else:
            pd.DataFrame([summary_data]).to_csv(summary_file, mode='w', header=True, index=False)
            self.stdout.write(self.style.SUCCESS(f"📊 Summary file created: {summary_file}"))

        # --- Print summary to console ---
        self.stdout.write("\n📈 === MERGE SUMMARY ===")
        self.stdout.write(f"🔹 Total EDCS records     : {total_edcs}")
        self.stdout.write(f"🔹 Total TBLIS records    : {total_tblis}")
        self.stdout.write(f"✅ Matched records        : {total_matched}")
        self.stdout.write(f"⚠️ Unmatched records      : {total_missing}")
        self.stdout.write(f"📈 Match rate             : {match_percentage}%")

        self.stdout.write(self.style.SUCCESS("\n🏁 Process completed successfully."))
