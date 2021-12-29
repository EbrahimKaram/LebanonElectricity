from glob import glob
import pandas as pd
import json

files = glob("Exits/*_*.json")
# print(files)
print(len(files))


# TODO: Get the Station and Staion ID from File name and put in the DataFrame
dfs = []
for file in files:
    print(file)
    # names = file.replace(r'Exits\',"")
    names = file[6:]

    details = names.split('_ ')
    station_ID = details[0]
    station_name = details[1].replace(".json", "")
    print(station_ID, station_name)
    reader = open(file, 'r', encoding='utf-8')
    data = json.load(reader)
    print(data["results"])
    df = pd.DataFrame(data["results"])
    df["Station ID"] = station_ID
    df["Station Name"] = station_name
    dfs.append(df)
    print(df.head())

power_df = pd.concat(dfs)
power_df.to_csv("Data/PowerHousesData.csv", index=False)
