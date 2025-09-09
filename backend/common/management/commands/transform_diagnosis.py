import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Convert diagnosis CSV: rename columns and prepare for upload"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input", "-i",
            type=str,
            required=True,
            help="Path to input CSV file (internal format)"
        )
        parser.add_argument(
            "--output", "-o",
            type=str,
            required=True,
            help="Path to output CSV file (upload-ready format)"
        )

    def handle(self, *args, **options):
        input_csv = options["input"]
        output_csv = options["output"]

        self.stdout.write(f"Converting Diagnosis CSV:\n  Input: {input_csv}\n  Output: {output_csv}")

        # Load CSV
        df = pd.read_csv(input_csv, sep=None, engine="python")  # auto-detect delimiter
        df.columns = df.columns.str.strip()

        # Mapping from source columns → Diagnosis model fields
        column_mapping = {
            "pid": "PID",
            "tb_diagnosis": "TbDiagnosis",
            "tb_diagnosis_date": "TbDiagnosisDate",
            "tb_diagnosis_made": "TbDiagnosisMade",
            "diagnosis_made_other": "DiagnosisMadeOther",
            "bacteriological_diagnosis": "BacteriologicalDiagnosis",
            "clinician_received_date": "ClinicianReceivedDate",
            "tb_register_number": "TbRegisterNumber",
            "tb_diagnosed_clinically": "TbDiagnosedClinically",
            "tb_clinically_other": "TbClinicallyOther",
            "tb_treatment": "TbTreatment",
            "tb_treatment_date": "TbTreatmentDate",
            "tb_facility": "TbFacility",
            "tb_reason": "TbReason",
            "tb_regimen": "TbRegimen",
            "tb_regimen_other": "TbRegimenOther",
            "regimen_changed": "RegimenChanged",
            "tb_otcome2": "TbOutcome2",
            "tb_otcome2_date": "TbOutcome2Date",
            "remarks": "Remarks",
        }

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Handle date columns
        date_columns = [
            "TbDiagnosisDate",
            "ClinicianReceivedDate",
            "TbTreatmentDate",
            "TbOutcome2Date",
            "XpertTruenatDate",
            "OtherBacteriologicalDate",
        ]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[col] = df[col].dt.strftime("%Y-%m-%d")

        # Keep only model-relevant columns
        upload_columns = [
            "PID",
            "TbDiagnosis",
            "TbDiagnosisDate",
            "TbDiagnosisMade",
            "DiagnosisMadeOther",
            "BacteriologicalDiagnosis",
            "TbDiagnosedClinically",
            "TbClinicallyOther",
            "ClinicianReceivedDate",
            "TbTreatment",
            "TbTreatmentDate",
            "TbFacility",
            "TbReason",
            "TbRegisterNumber",
            "TbRegimen",
            "TbRegimenOther",
            "RegimenChanged",
            "TbOutcome2",
            "TbOutcome2Date",
            "Remarks",
        ]
        df = df[[col for col in upload_columns if col in df.columns]]

        # Save output
        df.to_csv(output_csv, index=False)
        self.stdout.write(self.style.SUCCESS(f"Diagnosis CSV successfully converted to {output_csv}"))
