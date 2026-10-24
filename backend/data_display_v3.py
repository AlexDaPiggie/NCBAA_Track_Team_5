
import pandas as pd
import matplotlib.pyplot as plt

# Load the filtered LAX flight data
df = pd.read_csv("backend/data/lax_super_bowl_week.csv")
df["FL_DATE"] = pd.to_datetime(df["FL_DATE"])

# Keep only flights arriving at LAX with valid actual arrival times
df = df[
    (df["DEST"] == "LAX") &
    (df["CANCELLED"].fillna(0) == 0)
].copy()

# Convert arrival times (HHMM format) to hours (0-23)
arr_time = pd.to_numeric(df["ARR_TIME"], errors="coerce")

valid = (
    arr_time.between(0, 2359) &
    (arr_time % 100 < 60)
)

df = df[valid].copy()
df["ArrHour"] = (arr_time[valid] // 100).astype(int)

# Count arrivals for each day and hour
hourly_arrivals = (
    df.groupby([df["FL_DATE"].dt.strftime("%Y-%m-%d"), "ArrHour"])
      .size()
      .unstack(fill_value=0)
)

# Ensure every hour from 0 to 23 appears
hourly_arrivals = hourly_arrivals.reindex(
    columns=range(24), fill_value=0
)

# Plot one line per day
plt.figure(figsize=(14, 7))

for day, counts in hourly_arrivals.iterrows():
    plt.plot(
        range(24),
        counts.values,
        marker="o",
        label=day
    )

plt.xticks(range(24), [f"{h:02d}:00" for h in range(24)])
plt.xlabel("Hour of day (LAX local time)")
plt.ylabel("Number of arriving flights")
plt.title("Hourly LAX Arrivals by Day — Super Bowl Week 2022")
plt.legend(title="Flight date", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig("lax_arrivals_by_day.png", dpi=200)
plt.show()

print(hourly_arrivals)
