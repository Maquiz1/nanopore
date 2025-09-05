import pandas as pd

# Input CSV (internal/upload-ready CSV)
input_csv = "screening_form.csv"  # replace with your file
# Output CSV (download template)
output_csv = "screening_download.csv"

# Load the CSV
df = pd.read_csv(input_csv)

# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Mapping from upload columns to download template columns
column_mapping = {
    "pid": "PID",
    "screening_date": "ScreeningDate",
    "sex": "Sex",
    "dob": "DOB",
    "age": "Age",
    "present_symptoms": "PresentSymptoms",
    "genexpert_confirmation": "GenexpertConfirmation",
    "produce_resp_sample": "ProduceRespSample",
    "age18years": "Age18Years",
    "consent": "Consent",
    "consent_date": "ConsentDate",
    "not_willing": "NotWilling",
    "unable_understand": "UnableUnderstand",
    "enrolled": "Enrolled",
    "reasons": "Reasons",
    "reasons_other": "OtherReason",
    "remarks": "Remarks",
    "eligible": "Eligible",
    "facility_id": "Site",
    "zone": "Zone"
}

# Rename columns
df = df.rename(columns=column_mapping)

# Reorder columns to match download template
download_columns = [
    "PID",
    "ScreeningDate",
    "Sex",
    "DOB",
    "Age",
    "PresentSymptoms",
    "GenexpertConfirmation",
    "ProduceRespSample",
    "Age18Years",
    "Consent",
    "ConsentDate",
    "NotWilling",
    "UnableUnderstand",
    "Enrolled",
    "Reasons",
    "OtherReason",
    "Remarks",
    "Eligible",
    "Site",
    "Zone"
]

df = df[download_columns]

# Save the CSV in download template format
df.to_csv(output_csv, index=False)

print(f"Converted CSV saved as: {output_csv}")
