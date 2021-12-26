# Reference: https://www.w3schools.com/python/ref_requests_post.asp
import requests
import pandas as pd

url = 'https://www.edl.gov.lb/feedingdata.php'
stations_df = pd.read_csv("StationIDs.csv")
# print(stations_df.head())
# print(stations_df.columns)
for index, row in stations_df.iterrows():
    print(row['ID'], row[' Station Name'])
    myobj = {'mode': 'feeders-sel2', 'id': row['ID']}
    # verify needs to be false since SSL is expired
    x = requests.post(url, data=myobj, verify=False)
    with open('Exits/' + str(row['ID']) + "_" + row[' Station Name'] + '.json', 'w', encoding="utf-8") as f:
        f.write(x.text)
    print(x.text)
