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
        
        #13(a). Rifampicin
        # --- Step 1:  ---
        if "ljdst1_rifampicin" in merged_df.columns:
            merged_df["rifampicin"] = merged_df["ljdst1_rifampicin"].map(phenotypic_results_map)
        else:
            merged_df["rifampicin"] = None
        
        # --- Step 2: Override using MGIT DST if needed ---
        if "mgitdst1_rifampicin" in merged_df.columns:
        # Map mgit dst results first
            merged_df["mgit_rifampicin_tmp"] = merged_df["mgitdst1_rifampicin"].map(phenotypic_results_map)

            # Override if phenotypic_results is 5 OR NaN/empty
            merged_df.loc[
                (merged_df["rifampicin"].isna()) | 
                (merged_df["rifampicin"] == 5),
                "rifampicin"
            ] = merged_df["mgit_rifampicin_tmp"]

            # Clean temporary column
            merged_df.drop(columns=["mgit_rifampicin_tmp"], inplace=True, errors="ignore")
            
        merged_df.drop(columns=["ljdst1_rifampicin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst1_rifampicin"], inplace=True, errors="ignore")
            
        #13(b). Isoniazid:
        # --- Step 1:  ---
        if "ljdst1_isoniazid" in merged_df.columns:
            merged_df["isoniazid"] = merged_df["ljdst1_isoniazid"].map(phenotypic_results_map)
        else:
            merged_df["isoniazid"] = None
        
        # --- Step 2: Override using MGIT DST if needed ---
        if "mgitdst1_isoniazid" in merged_df.columns:
        # Map mgit dst results first
            merged_df["mgit_isoniazid_tmp"] = merged_df["mgitdst1_isoniazid"].map(phenotypic_results_map)

            # Override if phenotypic_results is 5 OR NaN/empty
            merged_df.loc[
                (merged_df["isoniazid"].isna()) | 
                (merged_df["isoniazid"] == 5),
                "isoniazid"
            ] = merged_df["mgit_isoniazid_tmp"]

            # Clean temporary column
            merged_df.drop(columns=["mgit_isoniazid_tmp"], inplace=True, errors="ignore")
            
        merged_df.drop(columns=["ljdst1_isoniazid"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst1_isoniazid"], inplace=True, errors="ignore")
            
        #13(c). Levofloxacin
        # --- Step 1:  ---
        if "mgitdst2_levofloxacin" in merged_df.columns:
            merged_df["levofloxacin"] = merged_df["mgitdst2_levofloxacin"].map(phenotypic_results_map)
        # else:
        #     merged_df["levofloxacin"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_levofloxacin"], inplace=True, errors="ignore")
        
        
        #13(e). Bedaquiline
        # --- Step 1:  ---
        if "mgitdst2_bedaquiline" in merged_df.columns:
            merged_df["bedaquiline"] = merged_df["mgitdst2_bedaquiline"].map(phenotypic_results_map)
        # else:
        #     merged_df["bedaquiline"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_bedaquiline"], inplace=True, errors="ignore")

        #13(f). Linezolid
        # --- Step 1:  ---
        if "mgitdst2_linezolid" in merged_df.columns:
            merged_df["linezolid"] = merged_df["mgitdst2_linezolid"].map(phenotypic_results_map)
        # else:
        #     merged_df["linezolid"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_linezolid"], inplace=True, errors="ignore")
        
        
        #13(g). Clofazimine
        # --- Step 1:  ---
        if "mgitdst2_clofazimine" in merged_df.columns:
            merged_df["clofazimine"] = merged_df["mgitdst2_clofazimine"].map(phenotypic_results_map)
        # else:
        #     merged_df["clofazimine"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_clofazimine"], inplace=True, errors="ignore")
     
        #13(h). Cycloserine
        # --- Step 1:  ---
        if "mgitdst2_cycloserine" in merged_df.columns:
            merged_df["cycloserine"] = merged_df["mgitdst2_cycloserine"].map(phenotypic_results_map)
        # else:
        #     merged_df["cycloserine"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_cycloserine"], inplace=True, errors="ignore")   
        
        #13(j). Ethambutol
        # --- Step 1:  ---
        if "ljdst1_ethambutol" in merged_df.columns:
            merged_df["ethambutol"] = merged_df["ljdst1_ethambutol"].map(phenotypic_results_map)
        else:
            merged_df["ethambutol"] = None
        
        # --- Step 2: Override using MGIT DST if needed ---
        if "mgitdst1_ethambutol" in merged_df.columns:
        # Map mgit dst results first
            merged_df["mgit_ethambutol_tmp"] = merged_df["mgitdst1_ethambutol"].map(phenotypic_results_map)

            # Override if phenotypic_results is 5 OR NaN/empty
            merged_df.loc[
                (merged_df["ethambutol"].isna()) | 
                (merged_df["ethambutol"] == 5),
                "ethambutol"
            ] = merged_df["mgit_ethambutol_tmp"]

            # Clean temporary column
            merged_df.drop(columns=["mgit_ethambutol_tmp"], inplace=True, errors="ignore")
            
        merged_df.drop(columns=["ljdst1_ethambutol"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst1_ethambutol"], inplace=True, errors="ignore") 
        
        
        #13(k). Delamanid
        # --- Step 1:  ---
        if "mgitdst2_delamanid" in merged_df.columns:
            merged_df["delamanid"] = merged_df["mgitdst2_delamanid"].map(phenotypic_results_map)
        # else:
        #     merged_df["cycloserine"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_delamanid"], inplace=True, errors="ignore") 
        
        
        #13(r). Ethionamide
        # --- Step 1:  ---
        if "mgitdst2_ethionamide" in merged_df.columns:
            merged_df["ethionamide"] = merged_df["mgitdst2_ethionamide"].map(phenotypic_results_map)
        # else:
        #     merged_df["cycloserine"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_ethionamide"], inplace=True, errors="ignore")
        
        
        #13(s). Prothionamide
        # --- Step 1:  ---
        if "mgitdst2_prothionamide" in merged_df.columns:
            merged_df["prothionamide"] = merged_df["mgitdst2_prothionamide"].map(phenotypic_results_map)
        # else:
        #     merged_df["cycloserine"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_prothionamide"], inplace=True, errors="ignore")
        
        
        #13(t). Para-aminosalicylic acid
        # --- Step 1:  ---
        if "mgitdst2_pas" in merged_df.columns:
            merged_df["para_aminosalicylic_acid"] = merged_df["mgitdst2_pas"].map(phenotypic_results_map)
        # else:
        #     merged_df["cycloserine"] = None
        
        # # --- Step 2: Override using MGIT DST if needed ---
        # if "mgitdst1_levofloxacin" in merged_df.columns:
        # # Map mgit dst results first
        #     merged_df["mgit_levofloxacin_tmp"] = merged_df["mgitdst1_levofloxacin"].map(phenotypic_results_map)

        #     # Override if phenotypic_results is 5 OR NaN/empty
        #     merged_df.loc[
        #         (merged_df["levofloxacin"].isna()) | 
        #         (merged_df["levofloxacin"] == 5),
        #         "levofloxacin"
        #     ] = merged_df["mgit_levofloxacin_tmp"]

        #     # Clean temporary column
        #     merged_df.drop(columns=["mgit_levofloxacin_tmp"], inplace=True, errors="ignore")
            
        # merged_df.drop(columns=["ljdst1_levofloxacin"], inplace=True, errors="ignore")
        merged_df.drop(columns=["mgitdst2_pas"], inplace=True, errors="ignore")
        
        #Xpert XDR
        # Standardize blanks
        # 14(a). Was Xpert XDR performed?
        merged_df["gxxdr_date"] = merged_df["gxxdr_date"].replace("", pd.NA)

        # Map xpert_xdr_performed
        merged_df["xpert_xdr_performed"] = merged_df["gxxdr_date"].notna().map({True: 1, False: 2})

        # --- Replace EDCS xpert_xdr_performed with TBLIS gxxdr_date if available ---
        # 14(b). Date of performing Xpert XDR testing?
        
        if "gxxdr_date" in merged_df.columns:
            # merged_df["date_sputum_received"] = merged_df["rctdate"].combine_first(
            #     merged_df["date_sputum_received"]
            # )
            merged_df["xpert_xdr_date_performed"] = merged_df["gxxdr_date"]
            
        merged_df.drop(columns=["gxxdr_date"], inplace=True, errors="ignore")
        
        
        # Map TBLIS Xpert XDR RESULTS to numeric codes       
        xpert_xdr_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistance Inferred","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 2),
            **dict.fromkeys(["Indeterminate","Resistance Indeterminate"], 3),
            **dict.fromkeys(["MTB Not Detected"], 0),
        }
        
        #15(a). Isoniazid
        # --- Step 1:  ---
        if "gxxdr_isoniazid" in merged_df.columns:
            merged_df["xpert_xdr_isoniazid"] = merged_df["gxxdr_isoniazid"].map(xpert_xdr_results_map)
            
        merged_df.drop(columns=["gxxdr_isoniazid"], inplace=True, errors="ignore")
        
        #15(b). Fluoroquinolones
        # --- Step 1:  ---
        if "gxxdr_flq" in merged_df.columns:
            merged_df["xpert_xdr_fluoroquinolones"] = merged_df["gxxdr_flq"].map(xpert_xdr_results_map)
            
        merged_df.drop(columns=["gxxdr_flq"], inplace=True, errors="ignore")
        
        #15(c). Amikacin
        # --- Step 1:  ---
        if "gxxdr_amikacin" in merged_df.columns:
            merged_df["xpert_xdr_amikacin"] = merged_df["gxxdr_amikacin"].map(xpert_xdr_results_map)
            
        merged_df.drop(columns=["gxxdr_amikacin"], inplace=True, errors="ignore")
        
        #15(d). Kanamycin
        # --- Step 1:  ---
        if "gxxdr_kanamycin" in merged_df.columns:
            merged_df["xpert_xdr_kanamycin"] = merged_df["gxxdr_kanamycin"].map(xpert_xdr_results_map)
            
        merged_df.drop(columns=["gxxdr_kanamycin"], inplace=True, errors="ignore")
        
        
        #15(e). Capreomycin
        # --- Step 1:  ---
        if "gxxdr_capreomycin" in merged_df.columns:
            merged_df["xpert_xdr_capreomycin"] = merged_df["gxxdr_capreomycin"].map(xpert_xdr_results_map)
            
        merged_df.drop(columns=["gxxdr_capreomycin"], inplace=True, errors="ignore")
        
        #15(f). Ethionamide
        # --- Step 1:  ---
        if "gxxdr_ethionamide" in merged_df.columns:
            merged_df["xpert_xdr_ethionamide"] = merged_df["gxxdr_ethionamide"].map(xpert_xdr_results_map)
            
        merged_df.drop(columns=["gxxdr_ethionamide"], inplace=True, errors="ignore")
        
        
        #First-Line LPA
        # Map TBLIS 17(c). MTB result on LPA1: to numeric codes       
        lpa1_mtb_results_map = {
            **dict.fromkeys(["MTBC Detected"], 1),
            **dict.fromkeys(["MTBC Not Detected"], 2),
            **dict.fromkeys(["Invalid"], 3),
        }
        
        #17(c). MTB result on LPA1:
        # --- Step 1:  ---
        if "lpa1_mtbc" in merged_df.columns:
            merged_df["lpa1_mtb"] = merged_df["lpa1_mtbc"].map(lpa1_mtb_results_map)
            
        merged_df.drop(columns=["lpa1_mtbc"], inplace=True, errors="ignore")
        
        
        # Map TBLIS 17(d). RIF result: to numeric codes       
        lpa1_rif_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 2),
            **dict.fromkeys(["Indeterminate","Resistance Indeterminate"], 3),
            **dict.fromkeys(["Resistance Inferred"], 4),
            **dict.fromkeys(["MTB Not Detected"], 0),
        }
        
        #17(d). RIF result:
        # --- Step 1:  ---
        if "lpa1_rifampicin" in merged_df.columns:
            merged_df["lpa1_rif"] = merged_df["lpa1_rifampicin"].map(lpa1_rif_results_map)
            
        merged_df.drop(columns=["lpa1_rifampicin"], inplace=True, errors="ignore")
        
        
        # Map TBLIS 17(e). INH result: to numeric codes       
        lpa1_inh_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 3),
            **dict.fromkeys(["Resistance Indeterminate","Indeterminate"], 4),
            **dict.fromkeys(["Resistance Inferred"], 5),
            **dict.fromkeys(["MTB Not Detected"], 0),
        }
        
        #17(e). INH result:
        # --- Step 1:  ---
        if "lpa1_isoniazid" in merged_df.columns:
            merged_df["lpa1_inh"] = merged_df["lpa1_isoniazid"].map(lpa1_inh_results_map)
            
        merged_df.drop(columns=["lpa1_isoniazid"], inplace=True, errors="ignore")
        
        
        #Second-Line LPA
        # Map TBLIS 19(c). MTB result on LPA2 to numeric codes       
        lpa2_mtb_results_map = {
            **dict.fromkeys(["MTBC Detected"], 1),
            **dict.fromkeys(["MTBC Not Detected"], 2),
            **dict.fromkeys(["Invalid"], 3),
        }
        
        #19(c). MTB result on LPA2
        # --- Step 1:  ---
        if "lpa2_mtbc" in merged_df.columns:
            merged_df["lpa2_mtb"] = merged_df["lpa2_mtbc"].map(lpa2_mtb_results_map)
            
        merged_df.drop(columns=["lpa2_mtbc"], inplace=True, errors="ignore")
        
        
        # Map TBLIS 19(d). RFluoroquinolones on LPA2 to numeric codes       
        lpa2_results_map = {
            **dict.fromkeys(["Resistance Detected","Resistant"], 1),
            **dict.fromkeys(["Resistance not Detected","Sensitive"], 2),
            **dict.fromkeys(["Indeterminate","Resistance Indeterminate"], 3),
            **dict.fromkeys(["Resistance Inferred"], 4),
            **dict.fromkeys(["MTB Not Detected"], 0),
        }
        
        #19(d). RFluoroquinolones on LPA2
        # --- Step 1:  ---
        if "lpa2_flq" in merged_df.columns:
            merged_df["lpa2_rfluoroquinolones"] = merged_df["lpa2_flq"].map(lpa2_results_map)
            
        merged_df.drop(columns=["lpa2_flq"], inplace=True, errors="ignore")
        
        
        #19(e). Aminoglycosides on LPA2
        # --- Step 1:  ---
        if "lpa2_ag_cp" in merged_df.columns:
            merged_df["lpa2_aminoglycosides"] = merged_df["lpa2_ag_cp"].map(lpa2_results_map)
            
        merged_df.drop(columns=["lpa2_ag_cp"], inplace=True, errors="ignore")
        
        #19(f). Kanamycin on LPA2
        # --- Step 1:  ---
        if "lpa2_low_kan" in merged_df.columns:
            merged_df["lpa2_kanamycin"] = merged_df["lpa2_low_kan"].map(lpa2_results_map)
            
        merged_df.drop(columns=["lpa2_low_kan"], inplace=True, errors="ignore")
        
            
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
