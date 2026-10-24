
import pandas as pd
import matplotlib.pyplot as plt

# Load your filtered BTS data
df = pd.read_csv("backend/data/lax_super_bowl_week.csv")

# Convert flight date
df["FL_DATE"] = pd.to_datetime(df["FL_DATE"])

# Separate LAX departures and arrivals
departures = df[df["ORIGIN"] == "LAX"].copy()
arrivals = df[df["DEST"] == "LAX"].copy()

# 1. Distribution of departure delays
plt.figure(figsize=(9, 5))
departures["DEP_DELAY"].dropna().plot.hist(
    bins=50, edgecolor="black"
)
plt.xlabel("Departure delay (minutes)")
plt.ylabel("Number of flights")
plt.title("Distribution of LAX Departure Delays")
plt.tight_layout()
plt.show()

# 2. Distribution of arrival delays
plt.figure(figsize=(9, 5))
arrivals["ARR_DELAY"].dropna().plot.hist(
    bins=50, edgecolor="black"
)
plt.xlabel("Arrival delay (minutes)")
plt.ylabel("Number of flights")
plt.title("Distribution of LAX Arrival Delays")
plt.tight_layout()
plt.show()

# 3. Daily flight volume
daily_departures = departures.groupby("FlightDate").size()
daily_arrivals = arrivals.groupby("FlightDate").size()

daily_counts = pd.DataFrame({
    "Departures": daily_departures,
    "Arrivals": daily_arrivals
}).fillna(0)

daily_counts.plot(
    kind="line", marker="o", figsize=(10, 5)
)
plt.xlabel("Date")
plt.ylabel("Number of flights")
plt.title("Daily LAX Flight Activity")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
