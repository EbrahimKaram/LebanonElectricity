import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

# === 1. Load all CSVs ===
folder_path = "D:\\Bob On call\\Documents\\My projects\\LebanonElectricity\\Cuttoff Times"  # change if different
all_files = glob.glob(os.path.join(folder_path, "*.csv"))

df_list = []
for file in all_files:
    try:
        temp_df = pd.read_csv(file, parse_dates=["TimeStamp"])
        df_list.append(temp_df)
    except Exception as e:
        print(f"Skipping {file} due to error: {e}")

df_all = pd.concat(df_list, ignore_index=True)
print(f"Loaded {len(df_all)} rows from {len(all_files)} CSV files.")

# === 2. Let user choose a station ===
stations = sorted(df_all["Station Name"].unique())
print("\nAvailable stations:")
for i, s in enumerate(stations):
    print(f"{i}: {s}")

choice = int(input("\nEnter station number to forecast: "))
station_name = stations[choice]

df_station = df_all[df_all["Station Name"] == station_name].copy()
print(f"\nSelected station: {station_name} ({len(df_station)} records)")

# === 3. Feature engineering ===
df_station["day_of_week"] = df_station["TimeStamp"].dt.dayofweek
df_station["hour_of_day"] = df_station["TimeStamp"].dt.hour
df_station["prev_hour_status"] = df_station["Electricity"].shift(1).fillna(0)

# Remove first row if NaN after shift
df_station = df_station.dropna()

# Features & target
X = df_station[["day_of_week", "hour_of_day", "prev_hour_status"]]
y = df_station["Electricity"]

# Train model
model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X, y)

# === 4. Weekly forecast ===
weekly_forecast = []
for day in range(7):
    for hour in range(24):
        avg_prev = df_station.loc[
            (df_station["day_of_week"] == day) & (df_station["hour_of_day"] == (hour - 1) % 24),
            "Electricity"
        ].mean()
        avg_prev = 0 if np.isnan(avg_prev) else avg_prev
        prob_on = model.predict_proba([[day, hour, avg_prev]])[0][1]
        weekly_forecast.append({
            "Day": day,
            "Hour": hour,
            "Prob_ON": round(prob_on, 2)
        })

forecast_df = pd.DataFrame(weekly_forecast)

# Map day numbers to names
day_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
           4: "Friday", 5: "Saturday", 6: "Sunday"}
forecast_df["Day"] = forecast_df["Day"].map(day_map)

# Pivot to table
forecast_table = forecast_df.pivot(index="Hour", columns="Day", values="Prob_ON")

# Save CSV
output_csv = f"weekly_forecast_{station_name}.csv"
forecast_table.to_csv(output_csv)
print(f"\nForecast saved to {output_csv}")

# === 5. Plot heatmap ===
plt.figure(figsize=(10, 6))
sns.heatmap(
    forecast_table,
    annot=True,
    cmap="YlGnBu",
    cbar_kws={'label': 'Probability of Electricity ON'},
    fmt=".2f"
)
plt.title(f"Weekly Electricity Availability Forecast — {station_name}")
plt.ylabel("Hour of Day")
plt.xlabel("Day of Week")
plt.tight_layout()
plt.show()
