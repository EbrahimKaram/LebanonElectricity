import pandas as pd
import numpy as np
import glob
import os
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm

# === 1. Load all CSVs ===
# This section is fine as it is, as you're already using glob and pd.concat
# which are efficient.

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

df_all["station_encoded"] = station_encoder.fit_transform(df_all["Station Name"])
df_all["exit_encoded"] = exit_encoder.fit_transform(df_all["Exit Name"])

# === 3. Feature engineering ===
df_all["day_of_week"] = df_all["TimeStamp"].dt.dayofweek
df_all["hour_of_day"] = df_all["TimeStamp"].dt.hour
df_all["prev_hour_status"] = df_all.groupby(
    ["Station Name", "Exit Name"]
)["Electricity"].shift(1).fillna(0)

df_all = df_all.dropna(subset=["prev_hour_status"])

# === 4. Train model ===
features = ["day_of_week", "hour_of_day",
            "prev_hour_status", "station_encoded", "exit_encoded"]
X = df_all[features]
y = df_all["Electricity"]

# The model training itself is typically a one-time, expensive step, but
# you're already using n_jobs=-1, which leverages all available cores.
model = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
model.fit(X, y)

# === 5. Generate forecasts (Optimized) ===
day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Create a single DataFrame for all possible forecast points
forecast_points = pd.DataFrame({
    'day_of_week': np.repeat(np.arange(7), 24),
    'hour_of_day': np.tile(np.arange(24), 7)
})

# Pre-calculate the average 'prev_hour_status'
avg_prev_status = df_all.groupby(
    ['day_of_week', 'hour_of_day']
)['Electricity'].mean().reset_index().rename(columns={'Electricity': 'prev_hour_status'})

forecast_points = pd.merge(forecast_points, avg_prev_status,
                           on=['day_of_week', 'hour_of_day'], how='left')

forecast_points['prev_hour_status'] = forecast_points['prev_hour_status'].fillna(0)

# CORRECTED: Get all unique station-exit pairs from the original data
unique_station_exit_pairs = df_all[['station_encoded', 'exit_encoded']].drop_duplicates()

# Create the full forecast dataset by combining the forecast points
# with all unique station/exit combinations
# 'unique_station_exit_pairs' now has two columns of equal length
X_pred_all = pd.merge(
    forecast_points.assign(key=1),
    unique_station_exit_pairs.assign(key=1),
    on='key'
).drop('key', axis=1)

# Now, make all predictions at once (vectorized)
features = ["day_of_week", "hour_of_day",
            "prev_hour_status", "station_encoded", "exit_encoded"]
probabilities = model.predict_proba(X_pred_all[features])[:, 1]
X_pred_all['has_power'] = np.round(probabilities, 2)

# === 6. Restructure and save JSON ===
all_forecasts = []
grouped = X_pred_all.groupby(['station_encoded', 'exit_encoded'])

# The rest of the code is fine, but you'll need to handle
# the inverse transform correctly since we're iterating over
# station-exit pairs.

# A more robust way to handle the inverse transform within the loop
# is to use the unique pairs directly.
unique_pairs_list = unique_station_exit_pairs.to_dict('records')

for pair in tqdm(unique_pairs_list, desc="Generating JSON"):
    station_enc = pair['station_encoded']
    exit_enc = pair['exit_encoded']

    station_name = station_encoder.inverse_transform([station_enc])[0]
    exit_name = exit_encoder.inverse_transform([exit_enc])[0]

    # Filter the predictions for this specific pair
    group = X_pred_all[(X_pred_all['station_encoded'] == station_enc) &
                       (X_pred_all['exit_encoded'] == exit_enc)]

    forecast_list = []
    for day in range(7):
        for hour in range(24):
            prob_on = group.loc[
                (group['day_of_week'] == day) & (group['hour_of_day'] == hour),
                'has_power'
            ].iloc[0]

            forecast_list.append({
                "day": day_names[day],
                "hour": hour,
                "has_power": prob_on
            })

    all_forecasts.append({
        "station": station_name,
        "exit": exit_name,
        "forecast": forecast_list
    })

# Save JSON
output_json = "all_forecasts_optimized.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(all_forecasts, f, ensure_ascii=False, indent=2)

print(f"\nForecast JSON saved to {output_json}")