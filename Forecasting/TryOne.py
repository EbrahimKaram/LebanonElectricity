import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# === 1. Load and preprocess ===

main_folder="D:\\Bob On call\\Documents\\My projects\\LebanonElectricity\\Cuttoff Times\\"
df = pd.read_csv(main_folder + "1_الغاز_18_ZONE.csv", parse_dates=["TimeStamp"])

# Extract time features
df["day_of_week"] = df["TimeStamp"].dt.dayofweek  # 0=Monday, 6=Sunday
df["hour_of_day"] = df["TimeStamp"].dt.hour
df["prev_hour_status"] = df["Electricity"].shift(1).fillna(0)

# Remove first row with NaN after shift
df = df.dropna()

# Features & target
X = df[["day_of_week", "hour_of_day", "prev_hour_status"]]
y = df["Electricity"]

# Train model on all available data
model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X, y)

# === 2. Weekly forecast ===
weekly_forecast = []
for day in range(7):
    for hour in range(24):
        avg_prev = df.loc[(df["day_of_week"] == day) & (df["hour_of_day"] == (hour - 1) % 24), "Electricity"].mean()
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

# Pivot to make table
forecast_table = forecast_df.pivot(index="Hour", columns="Day", values="Prob_ON")

# Save to CSV
forecast_table.to_csv("weekly_forecast_" + df["Station Name"].iloc[0] + "_" + df["Exit Name"].iloc[0] + ".csv")
print("Forecast saved to weekly_forecast.csv")

# === 3. Plot heatmap ===
plt.figure(figsize=(10, 6))
sns.heatmap(
    forecast_table,
    annot=True,
    cmap="YlGnBu",
    cbar_kws={'label': 'Probability of Electricity ON'},
    fmt=".2f"
)
plt.title("Weekly Electricity Availability Forecast " + df["Station Name"].iloc[0] + " — " + df["Exit Name"].iloc[0])
plt.ylabel("Hour of Day")
plt.xlabel("Day of Week")
plt.tight_layout()
plt.savefig("Weekly Electricity Availability Forecast " + df["Station Name"].iloc[0] + " — " + df["Exit Name"].iloc[0] + ".png")
plt.show()

