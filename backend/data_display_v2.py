
import pandas as pd
import matplotlib.pyplot as plt

# Load filtered BTS data
df = pd.read_csv("backend/data/lax_super_bowl_week.csv")

df["FL_DATE"] = pd.to_datetime(df["FL_DATE"])

# BTS times are usually local airport time in HHMM format.
# CRS = scheduled time; actual = recorded time.
def parse_bts_time(series):
    # Convert values like 5, 45, 930, 1545 to HH:MM
    s = pd.to_numeric(series, errors="coerce")
    valid = s.between(0, 2359) & (s % 100 < 60)

    result = pd.Series(float("nan"), index=series.index)
    result.loc[valid] = (s.loc[valid] // 100)
    return result

# Use actual departure/arrival times where available.
# Fall back to scheduled times for cancelled/missing actual times.
# Exclude cancelled flights from the counts.
df = df[df["CANCELLED"].fillna(0) == 0].copy()

dep_time = df["DEP_TIME"]
arr_time = df["ARR_TIME"]

df["DepHour"] = parse_bts_time(dep_time)
df["ArrHour"] = parse_bts_time(arr_time)

# Count LAX departures by hour
departures = (
    df[df["ORIGIN"] == "LAX"]
    .groupby("DepHour")
    .size()
    .reindex(range(24), fill_value=0)
)

# Count LAX arrivals by hour
arrivals = (
    df[df["DEST"] == "LAX"]
    .groupby("ArrHour")
    .size()
    .reindex(range(24), fill_value=0)
)

# Plot hourly flight counts
plt.figure(figsize=(11, 6))
plt.plot(range(24), arrivals.values, marker="o", label="Arrivals")
plt.plot(range(24), departures.values, marker="o", label="Departures")

plt.xticks(range(24), [f"{h:02d}:00" for h in range(24)], rotation=45)
plt.xlabel("Hour of day (local LAX time)")
plt.ylabel("Number of flights across the selected dates")
plt.title("Hourly LAX Arrivals and Departures — Super Bowl Week 2022")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("lax_hourly_flights.png", dpi=200)
plt.show()

print("Arrivals by hour:")
print(arrivals)
print("\nDepartures by hour:")
print(departures)
