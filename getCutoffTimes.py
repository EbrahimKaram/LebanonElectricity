import pandas as pd
import requests
from datetime import date, timedelta
import json


def getDataForExit(station_ID, exit_ID):
    today = pd.to_datetime("today")
    print(today.strftime('%Y-%m-%d'))
    two_weeks_ago = today - timedelta(days=15)
    print(two_weeks_ago.strftime('%Y-%m-%d'))
    url = 'https://www.edl.gov.lb/feedingdata.php'

    myobj = {'a_substations': station_ID, 'a_feeders': exit_ID,
             'd1': two_weeks_ago.strftime('%Y-%m-%d'), 'd2': today.strftime('%Y-%m-%d'), 'mode': 'load', 'actpre': 'act'}
    x = requests.post(url, data=myobj, verify=False)
    print(x.text)
    with open('Cuttoff Times/Baskinta.json', 'w', encoding="utf-8") as f:
        f.write(x.text)


if __name__ == '__main__':
    # 162,1D,10,البوشرية
    # the one above didn't have any data published. I prsume that the exit is just dead
    # 305	بسكنتا	18	بكفيا

    station_ID = 18
    exit_ID = 305
    reader = open("Cuttoff Times/Baskinta.json", encoding='utf-8')
    data = json.load(reader)
    df = pd.DataFrame(data["list_feeders"])
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
    df.to_csv("Cuttoff Times/Sample Baskinta.csv", index=False)
