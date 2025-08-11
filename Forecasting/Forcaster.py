import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import glob
import os
import json

# === 1. Load all CSVs ===
folder_path = r"D:\Bob On call\Documents\My projects\LebanonElectricity\Cuttoff Times"
all_files = glob.glob(os.path.join(folder_path, "*.csv"))

# Remove files that do not start with a number
all_files = [f for f in all_files if os.path.basename(f)[0].isdigit()]

print(f"Found {len(all_files)} CSV files.")

df_list = []
for file in all_files:
    try:
        temp_df = pd.read_csv(file, parse_dates=["TimeStamp"])
        df_list.append(temp_df)
    except Exception as e:
        print(f"Skipping {file} due to error: {e}")

df_all = pd.concat(df_list, ignore_index=True)
print(f"Loaded {len(df_all)} rows from {len(all_files)} CSV files.")

# === 2. Feature engineering ===
df_all = df_all.sort_values("TimeStamp").reset_index(drop=True)
df_all["day_of_week"] = df_all["TimeStamp"].dt.dayofweek  # 0=Mon
df_all["hour_of_day"] = df_all["TimeStamp"].dt.hour
df_all["prev_hour_status"] = df_all.groupby(["Station Name", "Exit Name"])[
    "Electricity"].shift(1).fillna(0)

# Remove NaNs created by shift
df_all = df_all.dropna(subset=["prev_hour_status"])

# Clean station and exit names before encoding
df_all["Station Name"] = df_all["Station Name"].fillna("Unknown").astype(str)
df_all["Exit Name"] = df_all["Exit Name"].fillna("Unknown").astype(str)

# Encode station and exit names to integers for the model
station_encoder = LabelEncoder()
exit_encoder = LabelEncoder()

df_all["station_encoded"] = station_encoder.fit_transform(
    df_all["Station Name"])
df_all["exit_encoded"] = exit_encoder.fit_transform(df_all["Exit Name"])

# === 3. Train one big model for all stations/exits ===
feature_cols = ["day_of_week", "hour_of_day",
                "prev_hour_status", "station_encoded", "exit_encoded"]
X = df_all[feature_cols]
y = df_all["Electricity"]

model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X, y)

# === 4. Generate predictions for each station/exit ===
output = []
day_map = {0: "Mon", 1: "Tue", 2: "Wed",
           3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

stations = df_all[["Station Name", "Station ID"]].drop_duplicates()
exits = df_all[["Station Name", "Exit Name", "Exit ID"]].drop_duplicates()

for _, exit_row in exits.iterrows():
    station_name = exit_row["Station Name"]
    exit_name = exit_row["Exit Name"]
    exit_id = exit_row["Exit ID"]
    station_id = stations.loc[stations["Station Name"]
                              == station_name, "Station ID"].values[0]

    station_enc = station_encoder.transform([station_name])[0]
    exit_enc = exit_encoder.transform([exit_name])[0]

    forecast_list = []
    for day in range(7):
        for hour in range(24):
            # historical avg prev_hour_status for this exit
            avg_prev = df_all.loc[
                (df_all["Station Name"] == station_name) &
                (df_all["Exit Name"] == exit_name) &
                (df_all["day_of_week"] == day) &
                (df_all["hour_of_day"] == (hour - 1) % 24),
                "Electricity"
            ].mean()
            avg_prev = 0 if np.isnan(avg_prev) else avg_prev

            prob_on = model.predict_proba(
                [[day, hour, avg_prev, station_enc, exit_enc]])[0][1]

            forecast_list.append({
                "day": day_map[day],
                "hour": hour,
                "has_power": int(prob_on >= 0.5)  # binary yes/no
            })

    output.append({
        "station": station_name,
        "exit": exit_name,
        "station_id": int(station_id) if not pd.isna(station_id) else None,
        "exit_id": int(exit_id) if not pd.isna(exit_id) else None,
        "forecast": forecast_list
    })

# === 5. Save JSON ===
with open("all_forecasts.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved forecasts for {len(output)} exits to all_forecasts.json")
