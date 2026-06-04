import re
import pandas as pd
from django.core.management.base import BaseCommand
from nanopore.models import EdcsTblisMergeSummary

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

        # --- Parse TBLIS date range from filename ---
        tblis_date_from = tblis_date_to = None
        tblis_filename = tblis_csv.replace("\\", "/").split("/")[-1]
        date_match = re.search(
            r'(\d{2}-\d{2}-\d{4})-to-(\d{2}-\d{2}-\d{4})',
            tblis_filename
        )
        if date_match:
            tblis_date_from = date_match.group(1)  # e.g. 01-01-2025
            tblis_date_to   = date_match.group(2)  # e.g. 02-06-2026

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
        # edcs_df = edcs_df[edcs_df["pid"].astype(str).str.startswith(allowed_prefixes)]
        # Split EDCS into zonal vs non-zonal
        mask = edcs_df["pid"].astype(str).str.startswith(allowed_prefixes)

        edcs_zonal = edcs_df[mask].copy()        # will be transformed
        edcs_non_zonal = edcs_df[~mask].copy()  # keep as-is


        # Ensure key columns are comparable as strings
        edcs_df["unique_lab_no"] = edcs_df["unique_lab_no"].astype(str).str.strip()
        tblis_df["labno"] = tblis_df["labno"].astype(str).str.strip()

        # --- Merge ---
        merged_df = pd.merge(
            edcs_zonal,
            tblis_df,
            how='left',
            left_on='unique_lab_no',
            right_on='labno',
            suffixes=('_edcs', '_tblis')
        )
        
        mismatched_dates = pd.DataFrame()
        # --- Replace EDCS date with TBLIS rctdate if available ---
        if "rctdate" in merged_df.columns:
            # Replace empty strings with NA so fillna works correctly
            rctdate_clean = merged_df["rctdate"].replace(r'^\s*$', pd.NA, regex=True)
            
            # --- Logging Discrepancies ---
            both_present_date = rctdate_clean.notna() & merged_df["date_sputum_received"].notna()
            date_mismatch = both_present_date & (
                rctdate_clean.astype(str).str.strip() != merged_df["date_sputum_received"].astype(str).str.strip()
            )
            
            if date_mismatch.any():
                mismatched_dates = merged_df.loc[date_mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_dates["field"] = "date_sputum_received"
                mismatched_dates["edcs_value"] = merged_df.loc[date_mismatch, "date_sputum_received"]
                mismatched_dates["tblis_value"] = rctdate_clean.loc[date_mismatch]

            merged_df["date_sputum_received"] = rctdate_clean.fillna(merged_df["date_sputum_received"])
            
        merged_df.drop(columns=["rctdate"], inplace=True, errors="ignore")
        
        # --- Culture Performed Logic ---
        def get_culture_performed(row):
            lj = row.get("lj_innocdate")

            # Treat empty or NaN as missing
            if lj == "" or pd.isna(lj):
                return 2   # No LJ → culture not performed (2)

            return 1       # LJ present → culture performed (1)

        merged_df["culture_performed"] = merged_df.apply(get_culture_performed, axis=1)
        
        appearance_map = {
            **dict.fromkeys(["Salivary", "Clear", "Colourless","Mucosalivary","Salivary"], 1),
            "Mucoid": 2,
            **dict.fromkeys(["Purulent","Turbid"], 3),
            "Mucopurulent": 4,
            **dict.fromkeys(["Bloody","Mucopurulent / Bloody"], 5),
            **dict.fromkeys(["Not Applicable", "Not Indicated","See Comment","Brown"], 6),
        }

        # Map TBLIS appearance to numeric codes
        if "appearance_tblis" in merged_df.columns:
            merged_df["appearance_tblis"] = merged_df["appearance_tblis"].map(appearance_map)
            # merged_df["appearance_tblis"] = merged_df["appearance_tblis"].map(appearance_map).fillna(0)

        mismatched_app = pd.DataFrame()
        # --- Replace EDCS appearance with TBLIS values if available ---
        if "appearance_tblis" in merged_df.columns:
            appearance_clean = merged_df["appearance_tblis"].replace(r'^\s*$', pd.NA, regex=True)
            if "appearance_edcs" in merged_df.columns:
                # --- Logging Discrepancies ---
                both_present_app = appearance_clean.notna() & merged_df["appearance_edcs"].notna()
                app_mismatch = both_present_app & (
                    appearance_clean.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                    merged_df["appearance_edcs"].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                )

                if app_mismatch.any():
                    mismatched_app = merged_df.loc[app_mismatch, ["pid", "unique_lab_no"]].copy()
                    mismatched_app["field"] = "appearance"
                    mismatched_app["edcs_value"] = merged_df.loc[app_mismatch, "appearance_edcs"]
                    mismatched_app["tblis_value"] = appearance_clean.loc[app_mismatch]

                merged_df["appearance_edcs"] = appearance_clean.fillna(merged_df["appearance_edcs"])
            else:
                merged_df["appearance_edcs"] = appearance_clean

        # --- Rename final appearance column ---
        merged_df.rename(columns={"appearance_edcs": "appearance"}, inplace=True)

        # --- Drop TBLIS appearance column ---
        merged_df.drop(columns=["appearance_tblis"], inplace=True, errors="ignore")


        mismatched_vol = pd.DataFrame()
        # --- Replace EDCS sample_volume with TBLIS volume if available ---
        if "volume" in merged_df.columns:
            volume_clean = merged_df["volume"].replace(r'^\s*$', pd.NA, regex=True)
            if "sample_volume" in merged_df.columns:
                # --- Logging Discrepancies ---
                both_present_vol = volume_clean.notna() & merged_df["sample_volume"].notna()
                vol_mismatch = both_present_vol & (
                    volume_clean.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                    merged_df["sample_volume"].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                )

                if vol_mismatch.any():
                    mismatched_vol = merged_df.loc[vol_mismatch, ["pid", "unique_lab_no"]].copy()
                    mismatched_vol["field"] = "sample_volume"
                    mismatched_vol["edcs_value"] = merged_df.loc[vol_mismatch, "sample_volume"]
                    mismatched_vol["tblis_value"] = volume_clean.loc[vol_mismatch]

                merged_df["sample_volume"] = volume_clean.fillna(merged_df["sample_volume"])
            else:
                merged_df["sample_volume"] = volume_clean
                
        merged_df.drop(columns=["volume"], inplace=True, errors="ignore")


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
                ], 6),
            }

        mismatched_mic_type = pd.DataFrame()
        mismatched_mic_date = pd.DataFrame()
        mismatched_mic_res = pd.DataFrame()

        # Clean TBLIS microscopy dates and results
        if "fm_date" in merged_df.columns:
            merged_df["fm_date"] = merged_df["fm_date"].replace(r'^\s*$', pd.NA, regex=True)
        if "zn_date" in merged_df.columns:
            merged_df["zn_date"] = merged_df["zn_date"].replace(r'^\s*$', pd.NA, regex=True)
        tblis_microscopy_date = merged_df.get("fm_date", pd.Series(pd.NA, index=merged_df.index)).combine_first(merged_df.get("zn_date", pd.Series(pd.NA, index=merged_df.index)))

        if "fm_res" in merged_df.columns:
            merged_df["fm_res"] = merged_df["fm_res"].replace(r'^\s*$', pd.NA, regex=True)
        if "zn_res" in merged_df.columns:
            merged_df["zn_res"] = merged_df["zn_res"].replace(r'^\s*$', pd.NA, regex=True)
        tblis_microscopy_res_raw = merged_df.get("fm_res", pd.Series(pd.NA, index=merged_df.index)).combine_first(merged_df.get("zn_res", pd.Series(pd.NA, index=merged_df.index)))
        tblis_microscopy_res = tblis_microscopy_res_raw.map(microscopy_results_map)

        # Infer TBLIS microscopy type (1 for ZN, 2 for FM)
        tblis_microscopy_type = pd.Series(pd.NA, index=merged_df.index)
        if "zn_date" in merged_df.columns or "zn_res" in merged_df.columns:
            tblis_microscopy_type.loc[merged_df.get("zn_date", pd.Series(pd.NA, index=merged_df.index)).notna() | merged_df.get("zn_res", pd.Series(pd.NA, index=merged_df.index)).notna()] = 1
        if "fm_date" in merged_df.columns or "fm_res" in merged_df.columns:
            tblis_microscopy_type.loc[merged_df.get("fm_date", pd.Series(pd.NA, index=merged_df.index)).notna() | merged_df.get("fm_res", pd.Series(pd.NA, index=merged_df.index)).notna()] = 2

        # 1. microscopy_type
        if "microscopy_type" in merged_df.columns:
            edcs_mic_type = merged_df["microscopy_type"].replace(r'^\s*$', pd.NA, regex=True)
            both_present_type = tblis_microscopy_type.notna() & edcs_mic_type.notna()
            type_mismatch = both_present_type & (
                tblis_microscopy_type.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                edcs_mic_type.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            )
            if type_mismatch.any():
                mismatched_mic_type = merged_df.loc[type_mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_mic_type["field"] = "microscopy_type"
                mismatched_mic_type["edcs_value"] = edcs_mic_type.loc[type_mismatch]
                mismatched_mic_type["tblis_value"] = tblis_microscopy_type.loc[type_mismatch]
            
            merged_df["microscopy_type"] = tblis_microscopy_type.fillna(edcs_mic_type).fillna(1).infer_objects(copy=False)
        else:
            merged_df["microscopy_type"] = tblis_microscopy_type.fillna(1).infer_objects(copy=False)

        # 2. microscopy_date
        if "microscopy_date" in merged_df.columns:
            edcs_mic_date = merged_df["microscopy_date"].replace(r'^\s*$', pd.NA, regex=True)
            both_present_date = tblis_microscopy_date.notna() & edcs_mic_date.notna()
            date_mismatch = both_present_date & (
                tblis_microscopy_date.astype(str).str.strip() != edcs_mic_date.astype(str).str.strip()
            )
            if date_mismatch.any():
                mismatched_mic_date = merged_df.loc[date_mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_mic_date["field"] = "microscopy_date"
                mismatched_mic_date["edcs_value"] = edcs_mic_date.loc[date_mismatch]
                mismatched_mic_date["tblis_value"] = tblis_microscopy_date.loc[date_mismatch]

            merged_df["microscopy_date"] = tblis_microscopy_date.fillna(edcs_mic_date)
        else:
            merged_df["microscopy_date"] = tblis_microscopy_date

        # 3. microscopy_results
        if "microscopy_results" in merged_df.columns:
            edcs_mic_res = merged_df["microscopy_results"].replace(r'^\s*$', pd.NA, regex=True)
            both_present_res = tblis_microscopy_res.notna() & edcs_mic_res.notna()
            res_mismatch = both_present_res & (
                tblis_microscopy_res.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                edcs_mic_res.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            )
            if res_mismatch.any():
                mismatched_mic_res = merged_df.loc[res_mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_mic_res["field"] = "microscopy_results"
                mismatched_mic_res["edcs_value"] = edcs_mic_res.loc[res_mismatch]
                mismatched_mic_res["tblis_value"] = tblis_microscopy_res.loc[res_mismatch]

            merged_df["microscopy_results"] = tblis_microscopy_res.fillna(edcs_mic_res)
        else:
            merged_df["microscopy_results"] = tblis_microscopy_res

        # Drop original columns
        merged_df.drop(columns=["fm_date", "zn_date", "fm_res", "zn_res"], inplace=True, errors="ignore")



        # --- Culture Method Logic ---
        # # Standardize blanks
        mismatched_culture_method = pd.DataFrame()
        if "lj_innocdate" in merged_df.columns:
            merged_df["lj_innocdate"] = merged_df["lj_innocdate"].replace(r'^\s*$', pd.NA, regex=True)
        if "mgit_entrydate" in merged_df.columns:
            merged_df["mgit_entrydate"] = merged_df["mgit_entrydate"].replace(r'^\s*$', pd.NA, regex=True)
            
        has_lj = merged_df.get("lj_innocdate", pd.Series(pd.NA, index=merged_df.index)).notna()
        has_mgit = merged_df.get("mgit_entrydate", pd.Series(pd.NA, index=merged_df.index)).notna()
        
        tblis_culture_method = pd.Series(pd.NA, index=merged_df.index)
        tblis_culture_method.loc[has_mgit] = "2"
        tblis_culture_method.loc[has_lj] = "1" # Prioritize LJ if both are present
        
        if "culture_method" in merged_df.columns:
            edcs_culture_method = merged_df["culture_method"].replace(r'^\s*$', pd.NA, regex=True)
            
            both_present_cm = tblis_culture_method.notna() & edcs_culture_method.notna()
            cm_mismatch = both_present_cm & (
                tblis_culture_method.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                edcs_culture_method.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            )
            
            if cm_mismatch.any():
                mismatched_culture_method = merged_df.loc[cm_mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_culture_method["field"] = "culture_method"
                mismatched_culture_method["edcs_value"] = edcs_culture_method.loc[cm_mismatch]
                mismatched_culture_method["tblis_value"] = tblis_culture_method.loc[cm_mismatch]
                
            merged_df["culture_method"] = tblis_culture_method.fillna(edcs_culture_method)
        else:
            merged_df["culture_method"] = tblis_culture_method



        mismatched_lj_innoc_date = pd.DataFrame()
        # --- Replace EDCS date with TBLIS lj_innocdate if available ---
        if "lj_innocdate" in merged_df.columns:
            lj_innoc_clean = merged_df["lj_innocdate"].replace(r'^\s*$', pd.NA, regex=True)
            if "lj_inoculation_date" in merged_df.columns:
                both_present_innoc = lj_innoc_clean.notna() & merged_df["lj_inoculation_date"].notna()
                innoc_mismatch = both_present_innoc & (
                    lj_innoc_clean.astype(str).str.strip() != merged_df["lj_inoculation_date"].astype(str).str.strip()
                )
                
                if innoc_mismatch.any():
                    mismatched_lj_innoc_date = merged_df.loc[innoc_mismatch, ["pid", "unique_lab_no"]].copy()
                    mismatched_lj_innoc_date["field"] = "lj_inoculation_date"
                    mismatched_lj_innoc_date["edcs_value"] = merged_df.loc[innoc_mismatch, "lj_inoculation_date"]
                    mismatched_lj_innoc_date["tblis_value"] = lj_innoc_clean.loc[innoc_mismatch]
                    
                merged_df["lj_inoculation_date"] = lj_innoc_clean.fillna(merged_df["lj_inoculation_date"])
            else:
                merged_df["lj_inoculation_date"] = lj_innoc_clean
                
        merged_df.drop(columns=["lj_innocdate"], inplace=True, errors="ignore")
        
        mismatched_lj_res_date = pd.DataFrame()
        # --- Replace EDCS date with TBLIS lj_date if available ---
        if "lj_date" in merged_df.columns:
            lj_date_clean = merged_df["lj_date"].replace(r'^\s*$', pd.NA, regex=True)
            if "lj_results_date" in merged_df.columns:
                both_present_lj_res = lj_date_clean.notna() & merged_df["lj_results_date"].notna()
                lj_res_mismatch = both_present_lj_res & (
                    lj_date_clean.astype(str).str.strip() != merged_df["lj_results_date"].astype(str).str.strip()
                )
                
                if lj_res_mismatch.any():
                    mismatched_lj_res_date = merged_df.loc[lj_res_mismatch, ["pid", "unique_lab_no"]].copy()
                    mismatched_lj_res_date["field"] = "lj_results_date"
                    mismatched_lj_res_date["edcs_value"] = merged_df.loc[lj_res_mismatch, "lj_results_date"]
                    mismatched_lj_res_date["tblis_value"] = lj_date_clean.loc[lj_res_mismatch]
                    
                merged_df["lj_results_date"] = lj_date_clean.fillna(merged_df["lj_results_date"])
            else:
                merged_df["lj_results_date"] = lj_date_clean
                
        merged_df.drop(columns=["lj_date"], inplace=True, errors="ignore")
        
        
        # --- Map LJ CULTURE results to numeric codes ---
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
            **dict.fromkeys(["POSITIVE   4+ AFBs Seen"], 8),
        }

        id_results_map = {
            **dict.fromkeys(["Mycobacteria other than M.tuberculosis","Negative"], 7),
            **dict.fromkeys([
                "Mycobacteria tuberculosis complex","Not Applicable","Not done",
                "Positive","Presumptive M.tuberculosis complex","See comment"
            ], 8),
        }

        # --- Map id_results ---
        if "id_res" in merged_df.columns:
            merged_df["id_res"] = merged_df["id_res"].map(id_results_map)

        # --- Map LJ results ---
        tblis_lj_results = pd.Series(pd.NA, index=merged_df.index)
        if "lj_res" in merged_df.columns:
            tblis_lj_results = merged_df["lj_res"].map(lj_results_map)

        # --- Override rule: if id_res == 7, replace lj_results with 7 ---
        if "id_res" in merged_df.columns:
            tblis_lj_results.loc[merged_df["id_res"] == 7] = 7
            
        mismatched_lj_res = pd.DataFrame()
        if "lj_results" in merged_df.columns:
            edcs_lj_res = merged_df["lj_results"].replace(r'^\s*$', pd.NA, regex=True)
            both_present_lj_res = tblis_lj_results.notna() & edcs_lj_res.notna()
            lj_res_mismatch = both_present_lj_res & (
                tblis_lj_results.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                edcs_lj_res.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            )
            if lj_res_mismatch.any():
                mismatched_lj_res = merged_df.loc[lj_res_mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_lj_res["field"] = "lj_results"
                mismatched_lj_res["edcs_value"] = edcs_lj_res.loc[lj_res_mismatch]
                mismatched_lj_res["tblis_value"] = tblis_lj_results.loc[lj_res_mismatch]
                
            merged_df["lj_results"] = tblis_lj_results.fillna(edcs_lj_res)
        else:
            merged_df["lj_results"] = tblis_lj_results

        # --- Drop intermediate column ---
        merged_df.drop(columns=["lj_res", "id_res"], inplace=True, errors="ignore")

        
        
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
        
        tblis_mgit_res = pd.Series(pd.NA, index=merged_df.index)
        if "mgit_res" in merged_df.columns:
            tblis_mgit_res = merged_df["mgit_res"].map(mgit_results_map)

        mismatched_mgit_res = pd.DataFrame()
        if "mgit_results" in merged_df.columns:
            edcs_mgit_res = merged_df["mgit_results"].replace(r'^\s*$', pd.NA, regex=True)
            both_present_mgit_res = tblis_mgit_res.notna() & edcs_mgit_res.notna()
            mgit_res_mismatch = both_present_mgit_res & (
                tblis_mgit_res.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                edcs_mgit_res.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            )
            if mgit_res_mismatch.any():
                mismatched_mgit_res = merged_df.loc[mgit_res_mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_mgit_res["field"] = "mgit_results"
                mismatched_mgit_res["edcs_value"] = edcs_mgit_res.loc[mgit_res_mismatch]
                mismatched_mgit_res["tblis_value"] = tblis_mgit_res.loc[mgit_res_mismatch]
                
            merged_df["mgit_results"] = tblis_mgit_res.fillna(edcs_mgit_res)
        else:
            merged_df["mgit_results"] = tblis_mgit_res

        merged_df.drop(columns=["mgit_res"], inplace=True, errors="ignore")

        # --- Drop TBLIS mgit_res column ---
        merged_df.drop(columns=["mgit_res"], inplace=True, errors="ignore")
        

        mismatched_phenotypic_date = pd.DataFrame()
        # Clean TBLIS phenotypic dates
        if "mgitdst1_date" in merged_df.columns:
            merged_df["mgitdst1_date"] = merged_df["mgitdst1_date"].replace(r'^\s*$', pd.NA, regex=True)
        if "mgitdst2_date" in merged_df.columns:
            merged_df["mgitdst2_date"] = merged_df["mgitdst2_date"].replace(r'^\s*$', pd.NA, regex=True)
        
        tblis_phenotypic_date = merged_df.get("mgitdst1_date", pd.Series(pd.NA, index=merged_df.index)).combine_first(
            merged_df.get("mgitdst2_date", pd.Series(pd.NA, index=merged_df.index))
        )
        
        if "phenotypic_date_results" in merged_df.columns:
            edcs_phenotypic_date = merged_df["phenotypic_date_results"].replace(r'^\s*$', pd.NA, regex=True)
            both_present_pheno_date = tblis_phenotypic_date.notna() & edcs_phenotypic_date.notna()
            pheno_date_mismatch = both_present_pheno_date & (
                tblis_phenotypic_date.astype(str).str.strip() != edcs_phenotypic_date.astype(str).str.strip()
            )
            
            if pheno_date_mismatch.any():
                mismatched_phenotypic_date = merged_df.loc[pheno_date_mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_phenotypic_date["field"] = "phenotypic_date_results"
                mismatched_phenotypic_date["edcs_value"] = edcs_phenotypic_date.loc[pheno_date_mismatch]
                mismatched_phenotypic_date["tblis_value"] = tblis_phenotypic_date.loc[pheno_date_mismatch]
                
            merged_df["phenotypic_date_results"] = tblis_phenotypic_date.fillna(edcs_phenotypic_date)
        else:
            merged_df["phenotypic_date_results"] = tblis_phenotypic_date

        merged_df.drop(columns=["mgitdst1_date", "mgitdst2_date"], inplace=True, errors="ignore")
        
        #Phenotypic DST RESULTS
        # Map TBLIS phenotypic_results to numeric codes       
        phenotypic_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistance Inferred","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 2),
            **dict.fromkeys(["Indeterminate","Resistance Indeterminate"], 3),
            **dict.fromkeys(["MTB Not Detected"], 5),
        }
        
        dst_mismatches = []

        def apply_dst_logic(merged_df, tblis_col, edcs_col, override_col=None):
            tblis_val = pd.Series(pd.NA, index=merged_df.index)
            if tblis_col in merged_df.columns:
                tblis_val = merged_df[tblis_col].map(phenotypic_results_map)
                
            if override_col and override_col in merged_df.columns:
                override_val = merged_df[override_col].map(phenotypic_results_map)
                override_mask = (tblis_val.isna() | (tblis_val == 5)) & override_val.notna()
                tblis_val.loc[override_mask] = override_val.loc[override_mask]

            mismatched = pd.DataFrame()
            if edcs_col in merged_df.columns:
                edcs_val = merged_df[edcs_col].replace(r'^\s*$', pd.NA, regex=True)
                both_present = tblis_val.notna() & edcs_val.notna()
                mismatch = both_present & (
                    tblis_val.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                    edcs_val.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                )
                if mismatch.any():
                    mismatched = merged_df.loc[mismatch, ["pid", "unique_lab_no"]].copy()
                    mismatched["field"] = edcs_col
                    mismatched["edcs_value"] = edcs_val.loc[mismatch]
                    mismatched["tblis_value"] = tblis_val.loc[mismatch]
                    
                merged_df[edcs_col] = tblis_val.fillna(edcs_val)
            else:
                merged_df[edcs_col] = tblis_val
                
            if not mismatched.empty:
                dst_mismatches.append(mismatched)
                
            cols_to_drop = [c for c in [tblis_col, override_col] if c]
            merged_df.drop(columns=cols_to_drop, inplace=True, errors="ignore")

        apply_dst_logic(merged_df, "ljdst1_rifampicin", "rifampicin", "mgitdst1_rifampicin")
        apply_dst_logic(merged_df, "ljdst1_isoniazid", "isoniazid", "mgitdst1_isoniazid")
        apply_dst_logic(merged_df, "mgitdst2_levofloxacin", "levofloxacin")
        apply_dst_logic(merged_df, "mgitdst2_bedaquiline", "bedaquiline")
        apply_dst_logic(merged_df, "mgitdst2_linezolid", "linezolid")
        apply_dst_logic(merged_df, "mgitdst2_clofazimine", "clofazimine")
        apply_dst_logic(merged_df, "mgitdst2_cycloserine", "cycloserine")
        apply_dst_logic(merged_df, "ljdst1_ethambutol", "ethambutol", "mgitdst1_ethambutol")
        apply_dst_logic(merged_df, "mgitdst2_delamanid", "delamanid")
        apply_dst_logic(merged_df, "mgitdst2_ethionamide", "ethionamide")
        apply_dst_logic(merged_df, "mgitdst2_prothionamide", "prothionamide")
        apply_dst_logic(merged_df, "mgitdst2_pas", "para_aminosalicylic_acid")
        
        #Xpert XDR
        mismatched_xpert_performed = pd.DataFrame()
        tblis_xpert_performed = pd.Series(pd.NA, index=merged_df.index)
        if "gxxdr_date" in merged_df.columns:
            merged_df["gxxdr_date"] = merged_df["gxxdr_date"].where(
                merged_df["gxxdr_date"].astype(str).str.strip() != "", other=pd.NA
            ).infer_objects(copy=False)
            tblis_xpert_performed = merged_df["gxxdr_date"].notna().map({True: 1, False: 2})
            
        if "xpert_xdr_performed" in merged_df.columns:
            edcs_xpert_performed = merged_df["xpert_xdr_performed"].replace(r'^\s*$', pd.NA, regex=True)
            both_present = tblis_xpert_performed.notna() & edcs_xpert_performed.notna()
            mismatch = both_present & (
                tblis_xpert_performed.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                edcs_xpert_performed.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            )
            
            if mismatch.any():
                mismatched_xpert_performed = merged_df.loc[mismatch, ["pid", "unique_lab_no"]].copy()
                mismatched_xpert_performed["field"] = "xpert_xdr_performed"
                mismatched_xpert_performed["edcs_value"] = edcs_xpert_performed.loc[mismatch]
                mismatched_xpert_performed["tblis_value"] = tblis_xpert_performed.loc[mismatch]
                
            merged_df["xpert_xdr_performed"] = tblis_xpert_performed.fillna(edcs_xpert_performed)
        else:
            merged_df["xpert_xdr_performed"] = tblis_xpert_performed

        # --- Replace EDCS xpert_xdr_performed with TBLIS gxxdr_date if available ---
        # 14(b). Date of performing Xpert XDR testing?
        mismatched_xpert_date = pd.DataFrame()
        if "gxxdr_date" in merged_df.columns:
            tblis_xpert_date = merged_df["gxxdr_date"]
            if "xpert_xdr_date_performed" in merged_df.columns:
                edcs_xpert_date = merged_df["xpert_xdr_date_performed"].replace(r'^\s*$', pd.NA, regex=True)
                both_present_date = tblis_xpert_date.notna() & edcs_xpert_date.notna()
                mismatch_date = both_present_date & (
                    tblis_xpert_date.astype(str).str.strip() != edcs_xpert_date.astype(str).str.strip()
                )
                if mismatch_date.any():
                    mismatched_xpert_date = merged_df.loc[mismatch_date, ["pid", "unique_lab_no"]].copy()
                    mismatched_xpert_date["field"] = "xpert_xdr_date_performed"
                    mismatched_xpert_date["edcs_value"] = edcs_xpert_date.loc[mismatch_date]
                    mismatched_xpert_date["tblis_value"] = tblis_xpert_date.loc[mismatch_date]
                
                merged_df["xpert_xdr_date_performed"] = tblis_xpert_date.fillna(edcs_xpert_date)
            else:
                merged_df["xpert_xdr_date_performed"] = tblis_xpert_date
                
        merged_df.drop(columns=["gxxdr_date"], inplace=True, errors="ignore")
        
        
        # Map TBLIS Xpert XDR RESULTS to numeric codes       
        xpert_xdr_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistance Inferred","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 2),
            **dict.fromkeys(["Indeterminate","Resistance Indeterminate"], 3),
            **dict.fromkeys(["MTB Not Detected"], 4),
        }
        
        xdr_mismatches = []

        def apply_xdr_logic(merged_df, tblis_col, edcs_col):
            tblis_val = pd.Series(pd.NA, index=merged_df.index)
            if tblis_col in merged_df.columns:
                tblis_val = merged_df[tblis_col].map(xpert_xdr_results_map)
                
            mismatched = pd.DataFrame()
            if edcs_col in merged_df.columns:
                edcs_val = merged_df[edcs_col].replace(r'^\s*$', pd.NA, regex=True)
                both_present = tblis_val.notna() & edcs_val.notna()
                mismatch = both_present & (
                    tblis_val.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                    edcs_val.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                )
                if mismatch.any():
                    mismatched = merged_df.loc[mismatch, ["pid", "unique_lab_no"]].copy()
                    mismatched["field"] = edcs_col
                    mismatched["edcs_value"] = edcs_val.loc[mismatch]
                    mismatched["tblis_value"] = tblis_val.loc[mismatch]
                    
                merged_df[edcs_col] = tblis_val.fillna(edcs_val)
            else:
                merged_df[edcs_col] = tblis_val
                
            if not mismatched.empty:
                xdr_mismatches.append(mismatched)
                
            merged_df.drop(columns=[tblis_col], inplace=True, errors="ignore")

        apply_xdr_logic(merged_df, "gxxdr_isoniazid", "xpert_xdr_isoniazid")
        apply_xdr_logic(merged_df, "gxxdr_flq", "xpert_xdr_fluoroquinolones")
        apply_xdr_logic(merged_df, "gxxdr_amikacin", "xpert_xdr_amikacin")
        apply_xdr_logic(merged_df, "gxxdr_kanamycin", "xpert_xdr_kanamycin")
        apply_xdr_logic(merged_df, "gxxdr_capreomycin", "xpert_xdr_capreomycin")
        apply_xdr_logic(merged_df, "gxxdr_ethionamide", "xpert_xdr_ethionamide")
        
        
        #First-Line LPA
        lpa_mismatches = []

        def apply_lpa_logic(merged_df, tblis_col, edcs_col, mapping_dict):
            tblis_val = pd.Series(pd.NA, index=merged_df.index)
            if tblis_col in merged_df.columns:
                tblis_val = merged_df[tblis_col].map(mapping_dict)
                
            mismatched = pd.DataFrame()
            if edcs_col in merged_df.columns:
                edcs_val = merged_df[edcs_col].replace(r'^\s*$', pd.NA, regex=True)
                both_present = tblis_val.notna() & edcs_val.notna()
                mismatch = both_present & (
                    tblis_val.astype(str).str.strip().str.replace(r'\.0$', '', regex=True) != 
                    edcs_val.astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                )
                if mismatch.any():
                    mismatched = merged_df.loc[mismatch, ["pid", "unique_lab_no"]].copy()
                    mismatched["field"] = edcs_col
                    mismatched["edcs_value"] = edcs_val.loc[mismatch]
                    mismatched["tblis_value"] = tblis_val.loc[mismatch]
                    
                merged_df[edcs_col] = tblis_val.fillna(edcs_val)
            else:
                merged_df[edcs_col] = tblis_val
                
            if not mismatched.empty:
                lpa_mismatches.append(mismatched)
                
            merged_df.drop(columns=[tblis_col], inplace=True, errors="ignore")

        # Map TBLIS 17(c). MTB result on LPA1: to numeric codes       
        lpa1_mtb_results_map = {
            **dict.fromkeys(["MTBC Detected"], 1),
            **dict.fromkeys(["MTBC Not Detected"], 2),
            **dict.fromkeys(["Invalid"], 3),
        }
        apply_lpa_logic(merged_df, "lpa1_mtbc", "lpa1_mtb", lpa1_mtb_results_map)
        
        # Map TBLIS 17(d). RIF result: to numeric codes       
        lpa1_rif_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 2),
            **dict.fromkeys(["Indeterminate","Resistance Indeterminate"], 3),
            **dict.fromkeys(["Resistance Inferred"], 4),
            **dict.fromkeys(["MTB Not Detected"], 5),
        }
        apply_lpa_logic(merged_df, "lpa1_rifampicin", "lpa1_rif", lpa1_rif_results_map)
        
        # Map TBLIS 17(e). INH result: to numeric codes       
        lpa1_inh_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 3),
            **dict.fromkeys(["Resistance Indeterminate","Indeterminate"], 4),
            **dict.fromkeys(["Resistance Inferred"], 5),
            **dict.fromkeys(["MTB Not Detected"], 7),
        }
        apply_lpa_logic(merged_df, "lpa1_isoniazid", "lpa1_inh", lpa1_inh_results_map)
        
        #Second-Line LPA
        # Map TBLIS 19(c). MTB result on LPA2 to numeric codes       
        lpa2_mtb_results_map = {
            **dict.fromkeys(["MTBC Detected"], 1),
            **dict.fromkeys(["MTBC Not Detected"], 2),
            **dict.fromkeys(["Invalid"], 3),
        }
        apply_lpa_logic(merged_df, "lpa2_mtbc", "lpa2_mtb", lpa2_mtb_results_map)
        
        # Map TBLIS 19(d). RFluoroquinolones on LPA2 to numeric codes       
        lpa2_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 2),
            **dict.fromkeys(["Indeterminate","Resistance Indeterminate"], 3),
            **dict.fromkeys(["Resistance Inferred"], 4),
            **dict.fromkeys(["MTB Not Detected"], 5),
        }
        apply_lpa_logic(merged_df, "lpa2_flq", "lpa2_rfluoroquinolones", lpa2_results_map)
        apply_lpa_logic(merged_df, "lpa2_ag_cp", "lpa2_aminoglycosides", lpa2_results_map)
        apply_lpa_logic(merged_df, "lpa2_low_kan", "lpa2_kanamycin", lpa2_results_map)
        
            
        # --- Keep only specific EDCS columns + all TBLIS columns ---
        edcs_cols = ["pid", "date_sputum_received", "unique_lab_no", "culture_performed"]
        existing_edcs_cols = [col for col in edcs_cols if col in merged_df.columns]
        tblis_cols = [col for col in merged_df.columns if col not in existing_edcs_cols]

        merged_df = merged_df[existing_edcs_cols + tblis_cols]

        # --- Summary Stats ---
        total_records = len(merged_df)
        matched_mask = merged_df["labno"].notna() if "labno" in merged_df.columns else pd.Series(True, index=merged_df.index)
        matched_records = matched_mask.sum()
        missing_records = total_records - matched_records

        # --- Missing summary (optional) ---
        if "labno" in merged_df.columns:
            missing_summary = merged_df[merged_df['labno'].isna()][["unique_lab_no"]]
            missing_summary.to_csv(output_csv.replace(".csv", "_missing.csv"), index=False)

        # merged_df = merged_df[["pid", "date_sputum_received", "unique_lab_no", "labno","appearance","sample_volume","volume","culture_performed","culture_method","microscopy_type"]]
        merged_df = merged_df[[
            "pid",
            "date_sputum_received",
            "appearance",
            "sample_volume",
            # "volume",
            "unique_lab_no",
            # "labno",

            "culture_performed",
            "culture_method",

            "microscopy_type",
            "microscopy_date",
            "microscopy_results",

            "lj_inoculation_date",
            "lj_results_date",
            "lj_results",

            "mgit_inoculation_date",
            "mgit_results_date",
            "mgit_results",

            "culture_isolate",
            "isolate_date",

            "phenotypic_performed",
            "phenotypic_date_performed",
            "phenotypic_date_results",

            # Phenotypic DST drugs
            "rifampicin",
            "isoniazid",
            "levofloxacin",
            "moxifloxacin",
            "bedaquiline",
            "linezolid",
            "clofazimine",
            "cycloserine",
            "terizidone",
            "ethambutol",
            "delamanid",
            "pyrazinamide",
            "imipenem",
            "cilastatin",
            "meropenem",
            "amikacin",
            "streptomycin",
            "ethionamide",
            "prothionamide",
            "para_aminosalicylic_acid",

            # Xpert XDR
            "xpert_xdr_performed",
            "xpert_xdr_date_performed",
            "xpert_xdr_isoniazid",
            "xpert_xdr_fluoroquinolones",
            "xpert_xdr_amikacin",
            "xpert_xdr_kanamycin",
            "xpert_xdr_capreomycin",
            "xpert_xdr_ethionamide",

            # First-line LPA
            "lpa",
            "first_line_lpa",
            "first_line_lpa_date",
            "first_line_drugs",
            "lpa1_mtb",
            "lpa1_rif",
            "lpa1_inh",

            # Second-line LPA
            "second_line_lpa",
            "second_line_lpa_date",
            "second_line_drugs",
            "lpa2_mtb",
            "lpa2_rfluoroquinolones",
            "lpa2_aminoglycosides",
            "lpa2_kanamycin",

            # Nanopore sequencing
            "nanopore_done",
            "sequencing_results",
            "epi_to_me",
            "epi_to_me_version",
            "nanopore_sequencing_date",
            "epi_to_me_date",
            "nanopore_results",
            "sequencing_delayed",
            "sequencing_delayed_days",
            "sequencing_delayed_reasons",
            "sequencing_delayed_others",

            # Nanopore DST results
            "nano_amikacin",
            "nano_bedaquiline",
            "nano_capreomycin",
            "nano_clofazimine",
            "nano_delamanid",
            "nano_ethambutol",
            "nano_ethionamide",
            "nano_isoniazid",
            "nano_kanamycin",
            "nano_levofloxacin",
            "nano_linezolid",
            "nano_moxifloxacin",
            "nano_pretomanid",
            "nano_pyrazinamide",
            "nano_rifampicin",
            "nano_streptomycin",
        ]]
        # --- Save Unmatched Records to separate files ---
        edcs_only = edcs_zonal[~edcs_zonal["unique_lab_no"].isin(tblis_df["labno"])]
        tblis_only = tblis_df[~tblis_df["labno"].isin(edcs_zonal["unique_lab_no"])]
        
        edcs_only_file = output_csv.replace(".csv", "_edcs_not_in_tblis.csv")
        tblis_only_file = output_csv.replace(".csv", "_tblis_not_in_edcs.csv")
        
        edcs_only.to_csv(edcs_only_file, index=False)
        tblis_only.to_csv(tblis_only_file, index=False)

        # Filter merged_df to ONLY include those that merged (labno is present)
        merged_df = merged_df[matched_mask]

        # Combine transformed zonal with untouched non-zonal
        final_df = pd.concat([merged_df, edcs_non_zonal], ignore_index=True)

        merged_df = final_df

        # --- Save output ---
        merged_df.to_csv(output_csv, index=False)

        total_columns = len(merged_df.columns)
        # print("Total number of columns:", len(selected_columns))

        # --- Output summary ---
        tblis_total_rows = len(tblis_df)
        edcs_only_count  = len(edcs_only)
        tblis_only_count = len(tblis_only)

        self.stdout.write(self.style.SUCCESS("\n✅ Merge Completed Successfully!"))
        self.stdout.write(f"📊 Total Columns: {total_columns}")
        self.stdout.write(f"📊 Total zonal records (EDCS): {total_records}")
        self.stdout.write(f"📊 Total TBLIS rows in file: {tblis_total_rows}")
        if tblis_date_from and tblis_date_to:
            self.stdout.write(f"📅 TBLIS Data Range: {tblis_date_from}  →  {tblis_date_to}")
        self.stdout.write(f"✅ Matched zonal records: {matched_records}")
        self.stdout.write(self.style.WARNING(f"⚠️  EDCS records NOT in TBLIS: {edcs_only_count}"))
        self.stdout.write(self.style.WARNING(f"⚠️  TBLIS records NOT in EDCS: {tblis_only_count}"))
        self.stdout.write(f"⚠️  Missing zonal records: {missing_records}")
        self.stdout.write(f"💾 Output saved to: {output_csv}")
        self.stdout.write(f"💾 Unmerged EDCS records saved to: {edcs_only_file}")
        self.stdout.write(f"💾 Unmerged TBLIS records saved to: {tblis_only_file}")
        # --- Save discrepancies ---
        all_mismatch_dfs = [
            mismatched_dates, mismatched_app, mismatched_vol,
            mismatched_mic_type, mismatched_mic_date, mismatched_mic_res,
            mismatched_culture_method, mismatched_lj_innoc_date, mismatched_lj_res_date,
            mismatched_lj_res, mismatched_mgit_res, mismatched_phenotypic_date,
            mismatched_xpert_performed, mismatched_xpert_date
        ] + dst_mismatches + xdr_mismatches + lpa_mismatches

        all_mismatches = pd.concat(
            [df for df in all_mismatch_dfs if not df.empty], 
            ignore_index=True
        ) if any(not df.empty for df in all_mismatch_dfs) else pd.DataFrame()
        
        if not all_mismatches.empty:
            mismatch_file = output_csv.replace(".csv", "_mismatches.csv")
            all_mismatches.to_csv(mismatch_file, index=False)
            self.stdout.write(self.style.WARNING(f"\n⚠️ Mismatched values found! Saved to: {mismatch_file}"))
            
            # Print mismatch summary
            self.stdout.write(self.style.WARNING("\n📊 Mismatch Summary by Field:"))
            mismatch_counts = all_mismatches["field"].value_counts()
            for field, count in mismatch_counts.items():
                self.stdout.write(f"   - {field}: {count} mismatches")
                
            total_mismatch_columns = len(mismatch_counts)
            total_mismatch_records = all_mismatches["pid"].nunique()
            
            self.stdout.write(self.style.WARNING(f"\n📈 Total Mismatched Columns: {total_mismatch_columns}"))
            self.stdout.write(self.style.WARNING(f"📈 Total Mismatched Records: {total_mismatch_records}"))
            self.stdout.write(f"\n⚠️ Missing records: {missing_records}")
        # --- Save summary to DB ---
        mismatch_by_field_dict = {}
        total_mismatch_columns = 0
        total_mismatch_records = 0
        if not all_mismatches.empty:
            mismatch_counts = all_mismatches["field"].value_counts()
            mismatch_by_field_dict = {k: int(v) for k, v in mismatch_counts.items()}
            total_mismatch_columns = len(mismatch_counts)
            total_mismatch_records = all_mismatches["pid"].nunique()

        EdcsTblisMergeSummary.objects.create(
            total_columns=total_columns,
            total_edcs_records=total_records,
            total_tblis_rows=len(tblis_df),
            matched_records=matched_records,
            missing_records=missing_records,
            edcs_not_in_tblis=edcs_only_count,
            tblis_not_in_edcs=tblis_only_count,
            tblis_date_from=tblis_date_from or "",
            tblis_date_to=tblis_date_to or "",
            total_mismatch_columns=total_mismatch_columns,
            total_mismatch_records=int(total_mismatch_records),
            mismatch_by_field=mismatch_by_field_dict,
        )
        self.stdout.write(self.style.SUCCESS("✅ Merge summary saved to database."))

        self.stdout.write("\n")
