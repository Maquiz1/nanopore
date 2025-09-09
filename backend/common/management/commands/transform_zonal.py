import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Convert Zonal Laboratory CSV: rename columns and format dates"

    def add_arguments(self, parser):
        parser.add_argument(
            '--input', '-i',
            type=str,
            required=True,
            help='Path to input CSV file (internal format)'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Path to output CSV file (upload-ready format)'
        )

    def handle(self, *args, **options):
        input_csv = options['input']
        output_csv = options['output']

        self.stdout.write(f"Converting Zonal Laboratory CSV:\n  Input: {input_csv}\n  Output: {output_csv}")

        # Load CSV (auto-detect delimiter)
        df = pd.read_csv(input_csv, sep=None, engine='python')
        df.columns = df.columns.str.strip()

        # Mapping CSV columns → ZonalLaboratory model fields
        column_mapping = {
            "pid": "PID",
            "culture_performed": "CulturePerformed",
            "culture_method": "CultureMethod",
            "culture_results": "CultureResults",
            "date_sputum_received": "DateSputumReceived",
            "appearance": "Appearance",
            "sample_volume": "SampleVolume",
            "unique_lab_no": "UniqueLabNo",
            "microscopy_type": "MicroscopyType",
            "microscopy_date": "MicroscopyDate",
            "lj_inoculation_date": "LJInoculationDate",
            "microscopy_results": "MicroscopyResults",
            "lj_results_date": "LJResultsDate",
            "lj_results": "LJResults",
            "mgit_inoculation_date": "MGITInoculationDate",
            "mgit_results_date": "MGITResultsDate",
            "mgit_results": "MGITResults",
            "culture_isolate": "CultureIsolate",
            "isolate_date": "IsolateDate",
            "phenotypic_performed": "PhenotypicPerformed",
            "phenotypic_date_performed": "PhenotypicDatePerformed",
            "phenotypic_date_results": "PhenotypicDateResults",
            # DST results
            "rifampicin": "Rifampicin",
            "isoniazid": "Isoniazid",
            "levofloxacin": "Levofloxacin",
            "moxifloxacin": "Moxifloxacin",
            "bedaquiline": "Bedaquiline",
            "linezolid": "Linezolid",
            "clofazimine": "Clofazimine",
            "cycloserine": "Cycloserine",
            "terizidone": "Terizidone",
            "ethambutol": "Ethambutol",
            "delamanid": "Delamanid",
            "pyrazinamide": "Pyrazinamide",
            "imipenem": "Imipenem",
            "cilastatin": "Cilastatin",
            "meropenem": "Meropenem",
            "amikacin": "Amikacin",
            "streptomycin": "Streptomycin",
            "ethionamide": "Ethionamide",
            "prothionamide": "Prothionamide",
            "para_aminosalicylic_acid": "ParaAminosalicylicAcid",
            # Xpert XDR
            "xpert_xdr_performed": "XpertXDRPerformed",
            "isoniazid2": "XpertXDRIsoniazid",
            "fluoroquinolones": "XpertXDRFluoroquinolones",
            "amikacin2": "XpertXDRAmiKacin",
            "kanamycin": "XpertXDRKanamycin",
            "capreomycin": "XpertXDRCapreomycin",
            "ethionamide2": "XpertXDREthionamide",
            "xpert_xdr_date_performed": "XpertXDRDatePerformed",
            # Nanopore results
            "nano_amikacin": "NanoAmikacin",
            "nano_bedaquiline": "NanoBedaquiline",
            "nano_capreomycin": "NanoCapreomycin",
            "nano_clofazimine": "NanoClofazimine",
            "nano_delamanid": "NanoDelamanid",
            "nano_ethambutol": "NanoEthambutol",
            "nano_ethionamide": "NanoEthionamide",
            "nano_isoniazid": "NanoIsoniazid",
            "nano_kanamycin": "NanoKanamycin",
            "nano_levofloxacin": "NanoLevofloxacin",
            "nano_linezolid": "NanoLinezolid",
            "nano_moxifloxacin": "NanoMoxifloxacin",
            "nano_pretomanid": "NanoPretomanid",
            "nano_pyrazinamide": "NanoPyrazinamide",
            "nano_rifampicin": "NanoRifampicin",
            "nano_streptomycin": "NanoStreptomycin",
            
            # "nano_cycloserine": "NanoCycloserine",
            # "nano_terizidone": "NanoTerizidone",
            # "nano_cilastatin": "NanoCilastatin",
            # "nano_imipenem": "NanoImipenem",
            # "nano_meropenem": "NanoMeropenem",
            # "nano_prothionamide": "NanoProthionamide",
            # "nano_para_aminosalicylic_acid": "NanoParaAminosalicylicAcid",
            # LPA
            "first_line_lpa": "FirstLineLPA",
            "first_line_lpa_date": "FirstLineLPADate",
            "first_line_drugs": "FirstLineDrugs",
            "second_line_lpa": "SecondLineLPA",
            "second_line_lpa_date": "SecondLineLPADate",
            "second_line_drugs": "SecondLineDrugs",
            "lpa1_mtb": "LPA1MTB",
            "lpa1_rif": "LPA1RIF",
            "lpa1_inh": "LPA1INH",
            "lpa2_mtb": "LPA2MTB",
            "lpa2_rfluoroquinolones": "LPA2RFluoroquinolones",
            "lpa2_aminoglycosides": "LPA2Aminoglycosides",
            "lpa2_kanamycin": "LPA2Kanamycin",
            # Misc
            "nanopore_done": "NanoporeDone",
            "sequencing_results": "SequencingResults",
            "epi_to_me": "EpiToMe",
            "epi_to_me_version": "EpiToMeVersion",
            "remarks": "Remarks",
        }

        # Apply renaming
        df = df.rename(columns=column_mapping)

        # Handle date fields safely
        date_columns = [
            "DateSputumReceived", "MicroscopyDate", "LJInoculationDate",
            "LJResultsDate", "MGITInoculationDate", "MGITResultsDate",
            "IsolateDate", "PhenotypicDatePerformed", "XpertXDRDatePerformed",
            "FirstLineLPADate", "SecondLineLPADate"
        ]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].dt.strftime('%Y-%m-%d')

        # Keep only mapped columns
        upload_columns = list(column_mapping.values())
        df = df[[col for col in upload_columns if col in df.columns]]

        # Save output
        df.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"Zonal Laboratory CSV successfully converted to {output_csv}"))
