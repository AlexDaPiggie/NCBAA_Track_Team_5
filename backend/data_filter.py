
import pandas as pd
from pathlib import Path

#file location
file_path = Path(__file__).parent / "data" / "T_ONTIME_REPORTING.csv"

df = pd.read_csv(file_path, low_memory=False)

# convert dates to time readable
df["FL_DATE"] = pd.to_datetime(df["FL_DATE"])

# filter February 7–15, 2022 super bowl week
start_date = "2022-02-07"
end_date = "2022-02-15"

lax_flights = df[
    df["FL_DATE"].between(start_date, end_date)
    & (
        df["ORIGIN"].eq("LAX")
        | df["DEST"].eq("LAX")
    )
].copy()

#save the filtered dataset
output_path = Path(__file__).parent / "data" / "lax_super_bowl_week.csv"
lax_flights.to_csv(output_path, index=False)

#display results
print(f"Total matching flights: {len(lax_flights)}")
print(f"Saved to: {output_path.resolve()}")
print(lax_flights[["FL_DATE", "ORIGIN", "DEST"]].head())
