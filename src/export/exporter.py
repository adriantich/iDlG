

# input file
input_file = "test_scan_results/OV121081.1_500_100_mean.parquet"

# output file
output_file = "OV121081.1_500_100_mean.csv"

import pandas as pd

# Read the parquet file
df = pd.read_parquet(input_file)

# Save as CSV
df.to_csv(output_file, index=False)