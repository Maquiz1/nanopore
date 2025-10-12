from django.core.management.base import BaseCommand
import pandas as pd
import os


class Command(BaseCommand):
    help = "Update Screening CSV with Enrollment data, report missing records, and save updated files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--screening_csv", type=str, required=True,
            help="Path to the Screening CSV file"
        )
        parser.add_argument(
            "--enrollment_csv", type=str, required=True,
            help="Path to the Enrollment CSV file"
        )
        parser.add_argument(
            "--output_csv", type=str, required=True,
            help="Path to save the updated Screening CSV file"
        )
        parser.add_argument(
            "--missing_csv", type=str, required=False,
            help="Path to save the missing records CSV file"
        )

    def handle(self, *args, **options):
        screening_csv = options["screening_csv"]
        enrollment_csv = options["enrollment_csv"]
        output_csv = options["output_csv"]
        missing_csv = options.get("missing_csv") or os.path.join(
            os.path.dirname(output_csv), "screening_missing_records.csv"
        )

        self.stdout.write(f"📂 Loading Screening CSV: {screening_csv}")
        self.stdout.write(f"📂 Loading Enrollment CSV: {enrollment_csv}")

        # ---------------- Facility mapping ----------------
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

        # ---------------- Load CSVs ----------------
        df_screening = pd.read_csv(screening_csv)
        df_enrollment = pd.read_csv(enrollment_csv)

        # ---------------- Merge to update main Screening CSV ----------------
        df_merged = df_screening.merge(
            df_enrollment[["enrollment_id", "age", "sex", "dob"]],
            how="left",
            left_on="id",
            right_on="enrollment_id",
            suffixes=("", "_enrollment")
        )

        for col in ["age", "sex", "dob"]:
            df_merged[col] = df_merged[f"{col}_enrollment"].combine_first(df_merged[col])

        df_merged.drop(columns=["enrollment_id"] +
                       [f"{col}_enrollment" for col in ["age", "sex", "dob"]],
                       inplace=True, errors="ignore")

        # Save updated main Screening CSV
        df_merged.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"✅ Updated Screening CSV saved to: {output_csv}"))

        # ---------------- Find missing records ----------------
        missing_mask = ((df_merged["age"].isna() & df_merged["dob"].isna()) |
                        (df_merged["sex"].isna()) |
                        (df_merged["sex"].astype(str).str.strip() == ""))

        missing_records = df_merged.loc[missing_mask].copy()

        if missing_records.empty:
            self.stdout.write(self.style.SUCCESS("🎉 No missing Age/DOB or Sex found."))
            return

        # ---------------- Merge to fill missing records CSV ----------------
        df_missing_updated = missing_records.merge(
            df_enrollment[["enrollment_id", "age", "sex", "dob"]],
            how="left",
            left_on="id",
            right_on="enrollment_id",
            suffixes=("", "_enrollment")
        )

        for col in ["age", "sex", "dob"]:
            df_missing_updated[col] = df_missing_updated[f"{col}_enrollment"].combine_first(df_missing_updated[col])

        df_missing_updated.drop(columns=["enrollment_id"] +
                                [f"{col}_enrollment" for col in ["age", "sex", "dob"]],
                                inplace=True, errors="ignore")

        # Map facility names
        if "facility_id" in df_missing_updated.columns:
            df_missing_updated["facility_name"] = df_missing_updated["facility_id"].map(site_mapping)

        # Save missing records CSV (with eligible)
        cols_to_export = [c for c in ["facility_id", "facility_name", "pid", "id", "age", "dob", "sex", "eligible"]
                          if c in df_missing_updated.columns]
        df_missing_updated.to_csv(missing_csv, index=False, columns=cols_to_export)

        count_missing = len(df_missing_updated)
        self.stdout.write(self.style.WARNING(f"⚠️ Missing records updated and saved to: {missing_csv} ({count_missing} records)"))
