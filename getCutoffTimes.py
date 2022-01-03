import pandas as pd
import requests
from datetime import date, timedelta
import json


def getDataForExit(station_ID, exit_ID):
    today = pd.to_datetime("today")
    print(today.strftime('%Y-%m-%d'))
    two_weeks_ago = today - timedelta(weeks=2)
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
    print(df.head())
