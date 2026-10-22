import pandas as pd

# input_file = '~/Documents/WORKS/NIMR/DREAM/TB_LIS/_2026/_2026_09_14/CTRL-TBLIS-DFN-AllData-RESULTS_01-01-2025-to-31-08-2026.csv'

# output_file = '~/Documents/WORKS/NIMR/DREAM/TB_LIS/_2026/_2026_09_14/CTRL-TBLIS-DFN-AllData-RESULTS_01-01-2025-to-31-08-2026_CONVERTED.csv'

# df = pd.read_csv(input_file)

input_file = '~/Documents/WORKS/NIMR/DREAM/TB_LIS/_2026/_2026_09_21/CTRL-TBLIS-DFN-AllData-SAMPLES_01-01-2025-to-21-09-2026.xlsx'

output_file = '~/Documents/WORKS/NIMR/DREAM/TB_LIS/_2026/_2026_09_21/CTRL-TBLIS-DFN-AllData-SAMPLES_01-01-2025-to-21-09-2026_CONVERTED.csv'

df = pd.read_excel(input_file)

date_columns = [
    'rctdate',
    'fm_date',
    'fm_entrydate',
    'zn_date',
    'lj_date',
    'lj_innocdate',
    'lj_entrydate',
    'mgit_date',
    'mgit_contdate',
    'mgit_entrydate',
    'id_date',
    'gxxdr_date',
    'lpa1_date',
    'lpa1_entrydate',
    'lpa2_date',
    'ljdst1_date',
    'LJDST1_SETUPDATE',
    'LJDST1_DFCDATE',
    'ljdst1_entrydate',
    'LJDST2_SETUPDATE',
    'LJDST2_DFCDATE',
    'ljdst2_entrydate',
    'mgitdst1_date',
    'mgitdst2_date'
]

for col in date_columns:
    if col in df.columns:

        # Keep track of which values originally contain a time
        original = df[col].astype(str).str.strip()
        has_time = original.str.contains(r'\d{1,2}:\d{2}', regex=True, na=False)

        # Convert to datetime
        converted = pd.to_datetime(
            df[col],
            errors='coerce',
            dayfirst=False
        )

        # Default: date only
        df[col] = converted.dt.strftime('%Y-%m-%d')

        # Add time only where the original value contained a time
        df.loc[has_time, col] = converted[has_time].dt.strftime(
            '%Y-%m-%d %H:%M:%S'
        )

# Save converted file
df.to_csv(output_file, index=False)

print("Conversion completed successfully.")
print(f"Saved to: {output_file}")

# Preview
print(df[date_columns].head())