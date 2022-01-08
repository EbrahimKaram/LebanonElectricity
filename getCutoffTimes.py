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


def getCSVData(jsondata):
    if(jsondata["list_feeders"][0]["dateoffeeding"] == None):
        print("We need to skip this one ",
              jsondata["list_feeders"][0]["dateoffeeding"])
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
    # 162,1D,10,البوشرية
    # the one above didn't have any data published. I presume that the exit is just dead or didn't have data for the period
    # 305	بسكنتا	18	بكفيا

    station_legend_df = pd.read_csv(
        "Data\PowerHousesData.csv", encoding="utf-8")

    for index, row in station_legend_df.iterrows():
        # if(index != 0):
        #     break
        print(row['Station Name'], row['Exit Name'])
        filename = "Cuttoff Times/" + str(row["Station ID"]) +\
            "_" + row["Station Name"] + "_" + \
            str(row["Exit ID"]) + "_" + row["Exit Name"] + ".csv"
        if(Path(filename).is_file()):
            print("This was already gotten")
            continue
        station_ID = int(row["Station ID"])
        exit_ID = int(row["Exit ID"])
        reader = getDataForExit(station_ID, exit_ID)

        jsondata = json.loads(reader)
        df = getCSVData(jsondata)
        if(not df.empty):
            df.to_csv("Cuttoff Times/" + str(row["Station ID"]) +
                      "_" + row["Station Name"] + "_" + str(row["Exit ID"]) + "_" + row["Exit Name"] + ".csv", index=False)
