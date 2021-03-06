import pandas as pd
import requests
from datetime import date, timedelta
from pathlib import Path
import json


def getDataForExit(station_ID, exit_ID, days_back=15):
    today = pd.to_datetime("today")
    print(today.strftime('%Y-%m-%d'))
    two_weeks_ago = today - timedelta(days=days_back)
    print(two_weeks_ago.strftime('%Y-%m-%d'))
    url = 'https://www.edl.gov.lb/feedingdata.php'

    myobj = {'a_substations': station_ID, 'a_feeders': exit_ID,
             'd1': two_weeks_ago.strftime('%Y-%m-%d'), 'd2': today.strftime('%Y-%m-%d'), 'mode': 'load', 'actpre': 'act'}
    x = requests.post(url, data=myobj, verify=False)

    # print(x.text)
    return x.text
    # with open('Cuttoff Times/Baskinta.json', 'w', encoding="utf-8") as f:
    #     f.write(x.text)


def getCSVData(jsondata, index):

    if jsondata["status"] == False:
        print("The status came back false for this one")
        with open("Cuttoff Times\ingnoreIndexes.txt", mode='a') as f:
            f.write(str(index) + "\n")
        return
    if(jsondata["list_feeders"][0]["dateoffeeding"] == None):
        print("We need to skip this one ",
              jsondata["list_feeders"][0]["dateoffeeding"])
        with open("Cuttoff Times\ingnoreIndexes.txt", mode='a') as f:
            f.write(str(index) + "\n")
        return
    df = pd.DataFrame(jsondata["list_feeders"])
# Reference
# https://pandas.pydata.org/docs/reference/api/pandas.wide_to_long.html

    df = pd.wide_to_long(df, stubnames='time',
                         i='dateoffeeding', j='hour of day')
    df.sort_values(["dateoffeeding", "hour of day"], inplace=True)
    df.reset_index(inplace=True)

    # To get the timestamp back
    # https://stackoverflow.com/questions/38355816/pandas-add-timedelta-column-to-datetime-column-vectorized
    df['dateoffeeding'] = pd.to_datetime(df['dateoffeeding'])

    df["TimeStamp"] = df["dateoffeeding"] + \
        pd.to_timedelta(df['hour of day'], 'h')

    df.drop(["dateoffeeding", "hour of day", "f_type", "s_type", "f_rank",
             "s_rank", "fid", "kadesha", "excepted"], axis=1, inplace=True)

    df.rename({'time': 'Electricity', 'substationname': 'Station Name', 'substationid': 'Station ID', 'feedername': 'Exit Name', 'feederid': 'Exit ID'},
              axis='columns', inplace=True)

    # Reference to sort the columns the way you like
    # https://stackoverflow.com/questions/13148429/how-to-change-the-order-of-dataframe-columns
    # columns_reorder = df.columns.to_list()
    # columns_reorder = [columns_reorder[-1]] + \
    #     [columns_reorder[-2]]+columns_reorder[2:-2]
    columns_wanted = ["TimeStamp", "Electricity", "id",
                      "Station Name", "Station ID", "Exit Name", "Exit ID"]
    df = df[columns_wanted]
    return df


if __name__ == '__main__':
    # 162,1D,10,????????????????
    # the one above didn't have any data published. I presume that the exit is just dead or didn't have data for the period
    # 305	????????????	18	??????????
    requests.packages.urllib3.disable_warnings()
    station_legend_df = pd.read_csv(
        "Data\PowerHousesData.csv", encoding="utf-8")

    for index, row in station_legend_df.iterrows():

        print(row['Station Name'], row['Exit Name'], index)
        # Exit Matar seems down
        indexes_to_ignore = []
        with open("Cuttoff Times\ingnoreIndexes.txt", mode='r') as f:
            indexes_to_ignore = f.read().splitlines()
            indexes_to_ignore = list(map(int, indexes_to_ignore))

        if(index in [59, 137, 172, 180, 188, 193, 195, 216, 217, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270] + indexes_to_ignore):
            print("We know these have a false status")
            continue
        filename = "Cuttoff Times/" + str(row["Station ID"]) +\
            "_" + row["Station Name"] + "_" + \
            str(row["Exit ID"]) + "_" + row["Exit Name"] + ".csv"
        if(Path(filename).is_file()):
            print("This was already gotten")
            continue
        station_ID = int(row["Station ID"])
        exit_ID = int(row["Exit ID"])
        reader = getDataForExit(station_ID, exit_ID, days_back=20)

        jsondata = json.loads(reader)
        df = getCSVData(jsondata, index)
        if(isinstance(df, pd.DataFrame)):
            df.to_csv("Cuttoff Times/" + str(row["Station ID"]) +
                      "_" + row["Station Name"] + "_" + str(row["Exit ID"]) + "_" + row["Exit Name"] + ".csv", index=False)
