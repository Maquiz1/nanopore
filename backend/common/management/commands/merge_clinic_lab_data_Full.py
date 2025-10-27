from django.core.management.base import BaseCommand
import pandas as pd
from django.apps import apps
from django.db.models import Q, Count

class Command(BaseCommand):
    help = "Merge EDCS/TBLIS for SubStudy 2 patients and generate Zonal/Site/Completed Treatment summary"

    def add_arguments(self, parser):
        parser.add_argument('--edcs', '-e', type=str, required=True, help='Path to EDCS CSV file')
        parser.add_argument('--tblis', '-t', type=str, required=True, help='Path to TBLIS CSV file')
        parser.add_argument('--output', '-o', type=str, required=True, help='Path to output CSV file (merged dataset)')

    def handle(self, *args, **options):
        edcs_csv = options['edcs']
        tblis_csv = options['tblis']
        output_csv = options['output']

        # --- Load CSVs ---
        edcs_df = pd.read_csv(edcs_csv, sep=None, engine='python')
        tblis_df = pd.read_csv(tblis_csv, sep=None, engine='python')

        # --- Clean column names ---
        edcs_df.columns = edcs_df.columns.str.strip()
        tblis_df.columns = tblis_df.columns.str.strip()
        edcs_df["unique_lab_no"] = edcs_df["unique_lab_no"].astype(str).str.strip()
        tblis_df["labno"] = tblis_df["labno"].astype(str).str.strip()

        # --- Get models ---
        Screening = apps.get_model('nanopore', 'Screening')
        Enrollment = apps.get_model('nanopore', 'Enrollment')
        ClinicLab = apps.get_model('nanopore', 'ClinicLaboratory')
        Diagnosis = apps.get_model('nanopore', 'Diagnosis')

        # --- Only SubStudy 2 patients ---
        sub2_labnos = ClinicLab.objects.filter(substudy='2').values_list('labno', flat=True)
        sub2_labnos = [str(l).strip() for l in sub2_labnos]
        edcs_df = edcs_df[edcs_df['unique_lab_no'].isin(sub2_labnos)]

        # --- Merge EDCS/TBLIS ---
        merged_df = pd.merge(
            edcs_df,
            tblis_df,
            how='left',
            left_on='unique_lab_no',
            right_on='labno',
            suffixes=('_edcs', '_tblis')
        )

        # --- Keep specific EDCS columns + all TBLIS columns ---
        edcs_cols = ["pid", "date_sputum_received", "unique_lab_no", "culture_performed"]
        existing_edcs_cols = [c for c in edcs_cols if c in merged_df.columns]
        tblis_cols = [c for c in merged_df.columns if c not in existing_edcs_cols]
        merged_df = merged_df[existing_edcs_cols + tblis_cols]

        # --- Matched / Missing stats ---
        total_records = len(merged_df)
        matched_records = merged_df["labno"].notna().sum() if "labno" in merged_df.columns else 0
        missing_records = total_records - matched_records
        matched_rate = (matched_records / total_records) * 100 if total_records > 0 else 0

        # --- Save missing CSV ---
        if "labno" in merged_df.columns:
            merged_df[merged_df['labno'].isna()][["unique_lab_no"]].to_csv(
                output_csv.replace(".csv", "_missing.csv"), index=False
            )

        # --- Save merged CSV ---
        merged_df.to_csv(output_csv, index=False)

        # --- Screening summary per Zonal/Site ---
        screening_summary = Screening.objects.filter(
            clinic_laboratory__substudy='2'
        ).values(
            'site__district__region__zone__name',
            'site__name'
        ).annotate(
            total_screened=Count('id'),
            total_eligible=Count('eligible', filter=Q(eligible=True))
        )

        # --- Enrollment total ---
        total_enrolled = Enrollment.objects.count()

        # --- Completed Treatment ---
        completed_treatment = Diagnosis.objects.filter(status='Completed Treatment').count()

        # --- Prepare summary CSV ---
        summary_list = []
        for s in screening_summary:
            summary_list.append({
                'zone_name': s['site__district__region__zone__name'],
                'site_name': s['site__name'],
                'total_screened': s['total_screened'],
                'total_eligible': s['total_eligible'],
                'substudy2_patients': len(sub2_labnos),
                'total_enrolled': total_enrolled,
                'completed_treatment': completed_treatment
            })

        summary_df = pd.DataFrame(summary_list)
        summary_df.to_csv(output_csv.replace(".csv", "_summary.csv"), index=False)

        self.stdout.write(self.style.SUCCESS(f"✅ Merge complete."))
        self.stdout.write(f"📊 Total records: {total_records}, Matched: {matched_records}, Missing: {missing_records}, Matched rate: {matched_rate:.2f}%")
        self.stdout.write(f"💾 Merged CSV: {output_csv}")
        self.stdout.write(f"💾 Summary CSV: {output_csv.replace('.csv', '_summary.csv')}")
        self.stdout.write(f"💾 Missing CSV: {output_csv.replace('.csv', '_missing.csv')}")
