import pandas as pd
import numpy as np
import glob
import os
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm

# === 1. Load all CSVs ===
folder_path = r"D:\Bob On call\Documents\My projects\LebanonElectricity\Cuttoff Times"
all_files = glob.glob(os.path.join(folder_path, "*.csv"))

# Keep only files starting with a digit
all_files = [f for f in all_files if os.path.basename(f)[0].isdigit()]

print(f"Found {len(all_files)} CSV files...")

df_list = []
for file in all_files:
    try:
        temp_df = pd.read_csv(file, parse_dates=["TimeStamp"])
        df_list.append(temp_df)
    except Exception as e:
        print(f"Skipping {file}: {e}")

df_all = pd.concat(df_list, ignore_index=True)
print(f"Loaded {len(df_all):,} rows from {len(all_files)} CSV files.")

# === 2. Clean + encode categorical features ===
df_all["Station Name"] = df_all["Station Name"].fillna("Unknown").astype(str)
df_all["Exit Name"] = df_all["Exit Name"].fillna("Unknown").astype(str)

station_encoder = LabelEncoder()
exit_encoder = LabelEncoder()

df_all["station_encoded"] = station_encoder.fit_transform(
    df_all["Station Name"])
df_all["exit_encoded"] = exit_encoder.fit_transform(df_all["Exit Name"])

# === 3. Feature engineering ===
df_all["day_of_week"] = df_all["TimeStamp"].dt.dayofweek
df_all["hour_of_day"] = df_all["TimeStamp"].dt.hour
df_all["prev_hour_status"] = df_all.groupby(
    ["Station Name", "Exit Name"]
)["Electricity"].shift(1).fillna(0)

# Drop any rows missing essential values
df_all = df_all.dropna(subset=["prev_hour_status"])

# === 4. Train model ===
features = ["day_of_week", "hour_of_day",
            "prev_hour_status", "station_encoded", "exit_encoded"]
X = df_all[features]
y = df_all["Electricity"]

model = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
model.fit(X, y)

# === 5. Generate forecasts ===
all_forecasts = []
day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

stations = df_all["Station Name"].unique()
exits = df_all["Exit Name"].unique()

for station in tqdm(stations, desc="Stations"):
    for exit_name in exits:
        station_enc = station_encoder.transform([station])[0]
        exit_enc = exit_encoder.transform([exit_name])[0]

        # Filter data for avg_prev calculation
        df_se = df_all[(df_all["Station Name"] == station) &
                       (df_all["Exit Name"] == exit_name)]

        if df_se.empty:
            continue  # skip exits that don't exist for this station

        forecast_list = []
        for day in range(7):
            for hour in range(24):
                prev_hour = (hour - 1) % 24
                avg_prev = df_se.loc[
                    (df_se["day_of_week"] == day) &
                    (df_se["hour_of_day"] == prev_hour),
                    "Electricity"
                ].mean()
                avg_prev = 0 if np.isnan(avg_prev) else avg_prev

                X_pred = pd.DataFrame([{
                    "day_of_week": day,
                    "hour_of_day": hour,
                    "prev_hour_status": avg_prev,
                    "station_encoded": station_enc,
                    "exit_encoded": exit_enc
                }])

                prob_on = model.predict_proba(X_pred)[0][1]

                forecast_list.append({
                    "day": day_names[day],
                    "hour": hour,
                    "has_power": round(prob_on, 2)
                })

        all_forecasts.append({
            "station": station,
            "exit": exit_name,
            "forecast": forecast_list
        })

# === 6. Save JSON ===
output_json = "all_forecasts.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(all_forecasts, f, ensure_ascii=False, indent=2)

print(f"\nForecast JSON saved to {output_json}")
