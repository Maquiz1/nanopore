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

        # Filter EDCS by pid prefixes
        allowed_prefixes = (
            "DF_TZ_SS2_14",
            "DF_TZ_SS2_15",
            "DF_TZ_SS2_16",
            "DF_TZ_SS2_17",
            "DF_TZ_SS2_18",
            "DF_TZ_SS2_19",
        )
        edcs_df = edcs_df[edcs_df["pid"].astype(str).str.startswith(allowed_prefixes)]

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
        
        # --- Replace EDCS date with TBLIS rctdate if available ---
        if "rctdate" in merged_df.columns:
            # merged_df["date_sputum_received"] = merged_df["rctdate"].combine_first(
            #     merged_df["date_sputum_received"]
            # )
            merged_df["date_sputum_received"] = merged_df["rctdate"]
            
        merged_df.drop(columns=["rctdate"], inplace=True, errors="ignore")
        
        # --- Culture Performed Logic ---
        def get_culture_performed(row):
            lj = row.get("lj_innocdate")

            # Treat empty or NaN as missing
            if lj == "" or pd.isna(lj):
                return 2   # No LJ → culture not performed (2)

            return 1       # LJ present → culture performed (1)

        merged_df["culture_performed"] = merged_df.apply(get_culture_performed, axis=1)


        # Appearance Mapping to numeric codes
        # appearance_map = {
        #     "Salivary": 1,
        #     "Mucoid": 2,
        #     "Purulent": 3,
        #     "Bloody": 5
        # }
        
        appearance_map = {
            **dict.fromkeys(["Salivary", "Clear", "Colourless","Mucosalivary","Salivary"], 1),
            "Mucoid": 2,
            **dict.fromkeys(["Purulent","Turbid"], 3),
            "Mucopurulent": 4,
            **dict.fromkeys(["Bloody","Mucopurulent / Bloody"], 5),
            **dict.fromkeys(["Not Applicable", "Not Indicated","See Comment","Brown"], 0),
        }

        
        # Map TBLIS appearance to numeric codes
        if "appearance_tblis" in merged_df.columns:
            merged_df["appearance_tblis"] = merged_df["appearance_tblis"].map(appearance_map)
            # merged_df["appearance_tblis"] = merged_df["appearance_tblis"].map(appearance_map).fillna(0)


        # --- Replace EDCS appearance with TBLIS values if available ---
        if "appearance_tblis" in merged_df.columns:
            # merged_df["appearance_edcs"] = merged_df["appearance_tblis"].combine_first(
            #     merged_df.get("appearance_edcs")
            # )
            merged_df["appearance_edcs"] = merged_df["appearance_tblis"]

        # --- Rename final appearance column ---
        merged_df.rename(columns={"appearance_edcs": "appearance"}, inplace=True)

        # --- Drop TBLIS appearance column ---
        merged_df.drop(columns=["appearance_tblis"], inplace=True, errors="ignore")


        # --- Replace EDCS dsample_volume with TBLIS volume if available ---
        if "volume" in merged_df.columns:
            merged_df["sample_volume"] = merged_df["volume"]
            
        merged_df.drop(columns=["volume"], inplace=True, errors="ignore")


        # --- Handle microscopy_type ---
        merged_df["microscopy_type"] = (
            merged_df["microscopy_type"]
            .replace("", None)          # convert empty string to NaN
            .fillna(1)                  # replace NaN with 1
        )
        
        
        # Standardize empty strings to NaN
        merged_df["fm_date"] = merged_df["fm_date"].replace("", None)
        merged_df["zn_date"] = merged_df["zn_date"].replace("", None)

        # Create final microscopy_date using fm_date first, then zn_date
        merged_df["microscopy_date"] = merged_df["fm_date"].combine_first(merged_df["zn_date"])

        # Drop original columns
        merged_df.drop(columns=["fm_date", "zn_date"], inplace=True, errors="ignore")


        # --- Map microscopy_results to numeric codes ---
        microscopy_results_map = {
            **dict.fromkeys(["NEGATIVE - No AFBs seen"], 1),
            **dict.fromkeys([
                "POSITIVE   1 AFBs / Length Seen","POSITIVE   2 AFBs / Length Seen","POSITIVE   3 AFBs / Length Seen","POSITIVE   4 AFBs / Length Seen","POSITIVE   5 AFBs / Length Seen",
                "POSITIVE   6 AFBs / Length Seen","POSITIVE   7 AFBs / Length Seen","POSITIVE   8 AFBs / Length Seen","POSITIVE   9 AFBs / Length Seen","POSITIVE   10 AFBs / Length Seen",
                "POSITIVE   11 AFBs / Length Seen","POSITIVE   12 AFBs / Length Seen","POSITIVE   13 AFBs / Length Seen","POSITIVE   14 AFBs / Length Seen","POSITIVE   15 AFBs / Length Seen",
                "POSITIVE   16 AFBs / Length Seen","POSITIVE   17 AFBs / Length Seen","POSITIVE   18 AFBs / Length Seen","POSITIVE   19 AFBs / Length Seen",
                ], 2),
            **dict.fromkeys(["POSITIVE   1+ AFBs Seen"], 3),
            **dict.fromkeys(["POSITIVE   2+ AFBs Seen"], 4),
            **dict.fromkeys(["POSITIVE   3+ AFBs Seen"], 5),
            **dict.fromkeys([
                "POSITIVE - 1 AFBs/100 fields seen","POSITIVE - 2 AFBs/100 fields seen","POSITIVE - 3 AFBs/100 fields seen","POSITIVE - 4 AFBs/100 fields seen","POSITIVE - 5 AFBs/100 fields seen",
                "POSITIVE - 6 AFBs/100 fields seen","POSITIVE - 7 AFBs/100 fields seen","POSITIVE - 8 AFBs/100 fields seen","POSITIVE - 9 AFBs/100 fields seen",
                "POSITIVE   20 AFBs / Length Seen","POSITIVE   21 AFBs / Length Seen","POSITIVE   22 AFBs / Length Seen","POSITIVE   23 AFBs / Length Seen","POSITIVE   24 AFBs / Length Seen","POSITIVE   25 AFBs / Length Seen",
                "POSITIVE   26 AFBs / Length Seen","POSITIVE   27 AFBs / Length Seen","POSITIVE   28 AFBs / Length Seen","POSITIVE   29 AFBs / Length Seen","POSITIVE   30 AFBs / Length Seen",
                ], 0),
            }
        
        # Map TBLIS microscopy_results to numeric codes
        # Standardize empty strings to NaN
        merged_df["fm_res"] = merged_df["fm_res"].replace("", None)
        merged_df["zn_res"] = merged_df["zn_res"].replace("", None)

        # Create final microscopy_results using fm_res first, then zn_res
        merged_df["microscopy_results"] = merged_df["fm_res"].combine_first(merged_df["zn_res"])

        # --- Apply mapping ---
        merged_df["microscopy_results"] = merged_df["microscopy_results"].map(microscopy_results_map)

        # Drop original columns
        merged_df.drop(columns=["fm_res", "zn_res"], inplace=True, errors="ignore")



        # --- Culture Method Logic ---
        # # Standardize blanks
        # merged_df["lj_innocdate"] = merged_df["lj_innocdate"].replace("", pd.NA)
        # merged_df["mgit_entrydate"] = merged_df["mgit_entrydate"].replace("", pd.NA)

        # # Initialize culture_method based on lj_innocdate
        # merged_df["culture_method"] = merged_df["lj_innocdate"].notna().map({True: 1, False: 2})

        # # Override with mgit_entrydate if exists
        # merged_df.loc[merged_df["mgit_entrydate"].notna(), "culture_method"] = 2

        def get_culture_method(row):
            lj = row.get("lj_innocdate")
            mgit = row.get("mgit_entrydate")

            # Standardize empty strings to NaN
            if lj == "" or pd.isna(lj):
                lj = None
            if mgit == "" or pd.isna(mgit):
                mgit = None

            # Both empty → blank value
            if lj is None and mgit is None:
                return ""

            # Both present → "1,2"
            if lj is not None and mgit is not None:
                return "1,2"

            # Only LJ present → "1"
            if lj is not None:
                return "1"

            # Only MGIT present → "2"
            if mgit is not None:
                return "2"

        merged_df["culture_method"] = merged_df.apply(get_culture_method, axis=1)



        # --- Replace EDCS date with TBLIS rctdate if available ---
        if "lj_innocdate" in merged_df.columns:
            merged_df["lj_inoculation_date"] = merged_df["lj_innocdate"]
            
        merged_df.drop(columns=["lj_innocdate"], inplace=True, errors="ignore")
        
        
        # --- Replace EDCS date with TBLIS rctdate if available ---
        if "lj_date" in merged_df.columns:
            merged_df["lj_results_date"] = merged_df["lj_date"]
            
        merged_df.drop(columns=["lj_date"], inplace=True, errors="ignore")
        
        
        # --- Map microscopy_results to numeric codes ---
        lj_results_map = {
            **dict.fromkeys([
                "POSITIVE - 1 Colony","POSITIVE - 2 Colonies","POSITIVE - 3 Colonies","POSITIVE - 4 Colonies","POSITIVE - 5 Colonies",
                "POSITIVE - 6 Colonies","POSITIVE - 7 Colonies","POSITIVE - 8 Colonies","POSITIVE - 9 Colonies","POSITIVE - 10 Colonies",
                "POSITIVE - 11 Colonies","POSITIVE - 12 Colonies","POSITIVE - 13 Colonies","POSITIVE - 14 Colonies","POSITIVE - 15 Colonies",
                "POSITIVE - 16 Colonies","POSITIVE - 17 Colonies","POSITIVE - 18 Colonies","POSITIVE - 19 Colonies","POSITIVE - 20 Colonies",
                "POSITIVE - 21 Colonies","POSITIVE - 22 Colonies","POSITIVE - 23 Colonies","POSITIVE - 24 Colonies","POSITIVE - 25 Colonies",
                "POSITIVE - 26 Colonies","POSITIVE - 27 Colonies","POSITIVE - 28 Colonies","POSITIVE - 29 Colonies","POSITIVE - 30 Colonies",
                "POSITIVE - 31 Colonies","POSITIVE - 32 Colonies","POSITIVE - 33 Colonies","POSITIVE - 34 Colonies","POSITIVE - 35 Colonies",
                "POSITIVE - 36 Colonies","POSITIVE - 37 Colonies","POSITIVE - 38 Colonies","POSITIVE - 39 Colonies","POSITIVE - 40 Colonies",
                "POSITIVE - 41 Colonies","POSITIVE - 42 Colonies","POSITIVE - 43 Colonies","POSITIVE - 44 Colonies","POSITIVE - 45 Colonies",
                "POSITIVE - 46 Colonies","POSITIVE - 47 Colonies","POSITIVE - 48 Colonies","POSITIVE - 49 Colonies","POSITIVE - 50 Colonies",
            ], 1),
            **dict.fromkeys(["POSITIVE - 1+ Colonies"], 2),
            **dict.fromkeys(["POSITIVE - 2+ Colonies","POSITIVE - More than 20 Colonies"], 3),
            **dict.fromkeys(["POSITIVE - 3+ Colonies","POSITIVE","POSITIVE - Confluent Growth","POSITIVE - Innumerable Colonies"], 4),
            **dict.fromkeys(["NEGATIVE"], 5),
            **dict.fromkeys(["CONTAMINATED"], 6),
            **dict.fromkeys(["POSITIVE   4+ AFBs Seen"], 0),
        }

        id_results_map = {
            **dict.fromkeys(["Mycobacteria other than M.tuberculosis","Negative"], 7),
            **dict.fromkeys([
                "Mycobacteria tuberculosis complex","Not Applicable","Not done",
                "Positive","Presumptive M.tuberculosis complex","See comment"
            ], 0),
        }

        # --- Map id_results ---
        if "id_res" in merged_df.columns:
            merged_df["id_res"] = merged_df["id_res"].map(id_results_map)

        # --- Map LJ results ---
        if "lj_res" in merged_df.columns:
            merged_df["lj_res"] = merged_df["lj_res"].map(lj_results_map)

        # --- Set final lj_results from TBLIS initially ---
        merged_df["lj_results"] = merged_df["lj_res"]

        # --- Override rule: if id_res == 7, replace lj_results with 7 ---
        merged_df.loc[merged_df["id_res"] == 7, "lj_results"] = 7

        # --- Drop intermediate column ---
        merged_df.drop(columns=["lj_res"], inplace=True, errors="ignore")
        merged_df.drop(columns=["id_res"], inplace=True, errors="ignore")

        
        
        # --- Replace EDCS date with TBLIS rctdate if available ---
        if "mgit_date" in merged_df.columns:
            merged_df["mgit_results_date"] = merged_df["mgit_date"]
            
        merged_df.drop(columns=["mgit_date"], inplace=True, errors="ignore")
        
        # --- Map mgit_results to numeric codes ---
        mgit_results_map = {
            **dict.fromkeys(["POSITIVE"], 1),
            **dict.fromkeys(["NEGATIVE"], 2),
            **dict.fromkeys(["Contaminated"], 3),
            **dict.fromkeys(["POSITIVE FOR NTM"], 4),
            }
        
        # Map TBLIS mgit_results to numeric codes
        if "mgit_res" in merged_df.columns:
            merged_df["mgit_res"] = merged_df["mgit_res"].map(mgit_results_map)

        # --- Replace EDCS mgit_results with TBLIS values if available ---
        if "mgit_res" in merged_df.columns:
            merged_df["mgit_results"] = merged_df["mgit_res"]

        # --- Rename final mgit_results column ---
        # merged_df.rename(columns={"mgit_results_edcs": "mgit_results"}, inplace=True)

        # --- Drop TBLIS mgit_res column ---
        merged_df.drop(columns=["mgit_res"], inplace=True, errors="ignore")
        

        # Standardize empty strings to NaN
        merged_df["mgitdst1_date"] = merged_df["mgitdst1_date"].replace("", None)
        merged_df["mgitdst2_date"] = merged_df["mgitdst2_date"].replace("", None)

        # Create final phenotypic_date_results using fm_date first, then zn_date
        merged_df["phenotypic_date_results"] = merged_df["mgitdst1_date"].combine_first(merged_df["mgitdst2_date"])

        # Drop original columns
        merged_df.drop(columns=["mgitdst1_date", "mgitdst2_date"], inplace=True, errors="ignore")
        
        #Phenotypic DST RESULTS
        # Map TBLIS phenotypic_results to numeric codes       
        phenotypic_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistance Inferred","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 2),
            **dict.fromkeys(["Indeterminate","Resistance Indeterminate"], 3),
            **dict.fromkeys(["MTB Not Detected"], 5),
        }
        
        if "mgitdst1_res" in merged_df.columns:
            merged_df["phenotypic_results"] = merged_df["mgitdst1_res"].map(phenotypic_results_map)
        
        
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
