import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from pathlib import Path


class Command(BaseCommand):
    help = "Merge EDCS + TBLIS (outer) and output matched / edcs_only / tblis_only Excel files"

    def add_arguments(self, parser):
        parser.add_argument("--edcs", required=True)
        parser.add_argument("--tblis", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):

        edcs_csv = options["edcs"]
        tblis_csv = options["tblis"]
        output_csv = options["output"]

        self.stdout.write("\n🔄 Loading CSVs...")

        if not Path(edcs_csv).exists():
            raise CommandError(f"EDCS file not found: {edcs_csv}")

        if not Path(tblis_csv).exists():
            raise CommandError(f"TBLIS file not found: {tblis_csv}")

        edcs_df = pd.read_csv(edcs_csv, sep=None, engine="python", dtype=str)
        tblis_df = pd.read_csv(tblis_csv, sep=None, engine="python", dtype=str)

        edcs_df.columns = edcs_df.columns.str.strip()
        tblis_df.columns = tblis_df.columns.str.strip()

        required_edcs = {"pid", "unique_lab_no"}
        required_tblis = {"labno"}

        if not required_edcs.issubset(edcs_df.columns):
            raise CommandError("EDCS missing required columns")

        if not required_tblis.issubset(tblis_df.columns):
            raise CommandError("TBLIS missing required columns")

        edcs_df["unique_lab_no"] = edcs_df["unique_lab_no"].str.strip()
        tblis_df["labno"] = tblis_df["labno"].str.strip()

        # ==================================================
        # PID PREFIX FILTER
        # ==================================================

        allowed_prefixes = (
            "DF_TZ_SS2_14",
            "DF_TZ_SS2_15",
            "DF_TZ_SS2_16",
            "DF_TZ_SS2_17",
            "DF_TZ_SS2_18",
            "DF_TZ_SS2_19",
        )

        mask = edcs_df["pid"].astype(str).str.startswith(allowed_prefixes)

        edcs_zonal = edcs_df.loc[mask].copy()
        edcs_non_zonal = edcs_df.loc[~mask].copy()

        self.stdout.write(f"Zonal EDCS: {len(edcs_zonal)}")
        self.stdout.write(f"Non-zonal EDCS: {len(edcs_non_zonal)}")

        # ==================================================
        # FULL OUTER MERGE
        # ==================================================

        merged_all = pd.merge(
            edcs_zonal,
            tblis_df,
            how="outer",
            left_on="unique_lab_no",
            right_on="labno",
            indicator=True,
            suffixes=("_edcs", "_tblis"),
        )

        matched_df = merged_all.loc[merged_all["_merge"] == "both"].copy()
        edcs_only_df = merged_all.loc[merged_all["_merge"] == "left_only"].copy()
        tblis_only_df = merged_all.loc[merged_all["_merge"] == "right_only"].copy()

        # ==================================================
        # TRANSFORMS ONLY ON MATCHED
        # ==================================================

        merged_df = matched_df.copy()

        if "rctdate" in merged_df.columns:
            merged_df["date_sputum_received"] = merged_df["rctdate"]

        merged_df.drop(columns=["rctdate"], inplace=True, errors="ignore")

        if "lj_innocdate" in merged_df.columns:
            merged_df["culture_performed"] = merged_df["lj_innocdate"].notna().map(
                lambda x: 1 if x else 2
            )
        else:
            merged_df["culture_performed"] = ""

        # ==================================================
        # RE-ATTACH UNTOUCHED NON-ZONAL
        # ==================================================

        final_matched = pd.concat(
            [merged_df, edcs_non_zonal],
            ignore_index=True
        )

        # ==================================================
        # OUTPUT
        # ==================================================

        matched_file = output_csv.replace(".csv", "_matched.xlsx")
        edcs_only_file = output_csv.replace(".csv", "_edcs_only.xlsx")
        tblis_only_file = output_csv.replace(".csv", "_tblis_only.xlsx")

        final_matched.to_excel(matched_file, index=False)
        edcs_only_df.to_excel(edcs_only_file, index=False)
        tblis_only_df.to_excel(tblis_only_file, index=False)

        # ==================================================
        # SUMMARY + QUALITY METRICS
        # ==================================================

        total_edcs = len(edcs_df)
        total_tblis = len(tblis_df)
        total_zonal_edcs = len(edcs_zonal)

        matched_count = len(matched_df)
        edcs_only_count = len(edcs_only_df)
        tblis_only_count = len(tblis_only_df)

        match_pct = (
            (matched_count / total_zonal_edcs) * 100
            if total_zonal_edcs > 0 else 0
        )

        self.stdout.write(self.style.SUCCESS("\n✅ Merge completed"))

        self.stdout.write("\n📊 COUNTS")
        self.stdout.write(f"Total EDCS records: {total_edcs}")
        self.stdout.write(f"Total TBLIS records: {total_tblis}")
        self.stdout.write(f"Zonal EDCS records: {total_zonal_edcs}")

        self.stdout.write("\n🔗 MERGE RESULTS")
        self.stdout.write(f"Matched: {matched_count}")
        self.stdout.write(f"EDCS only: {edcs_only_count}")
        self.stdout.write(f"TBLIS only: {tblis_only_count}")

        self.stdout.write(
            self.style.WARNING(
                f"\n📈 Match rate (zonal EDCS): {match_pct:.2f}%"
            )
        )

        self.stdout.write(f"\n📁 {matched_file}")
        self.stdout.write(f"📁 {edcs_only_file}")
        self.stdout.write(f"📁 {tblis_only_file}\n")

        # ==================================================
        # SUMMARY
        # ==================================================

        self.stdout.write(self.style.SUCCESS("\n✅ Merge completed"))
        self.stdout.write(f"Matched: {len(matched_df)}")
        self.stdout.write(f"EDCS only: {len(edcs_only_df)}")
        self.stdout.write(f"TBLIS only: {len(tblis_only_df)}")

        self.stdout.write(f"\n📁 {matched_file}")
        self.stdout.write(f"📁 {edcs_only_file}")
        self.stdout.write(f"📁 {tblis_only_file}\n")
