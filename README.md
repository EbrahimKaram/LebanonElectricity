# Background
There is a lot of electricity Cutoffs in Lebanon.

Now there is a website from EDL that provides when the Cutoffs would be.
https://www.edl.gov.lb/feeding.php

There are two fields
- `محطة` The station
- `مخرج` The Exit

The problem it's hard to know which station is related to my interest. It's better to get all that data making it a bit more accessible.

## The Stations
There are supposedly 78 stations in all of Lebanon
You can see the full list via the `Stations.txt`

## The Exits
Every one of those stations has several exits and it seems those exits are region specific.
the names are sometimes counties and areas but not always.
From our Analysis, we know that there are 993 exits in total.

The Exits per station can range from 1 to 41

`الحرج` station has the most exits (41)
`نهر ابراهيم 3` has the least exits (1)

`الحرج` is most probably located near the capital which would explain why it has so many exits.

On average, every station would have 13 exits but the standard deviation is 9. That would mean 68 percent of the stations have a value between 13-9 and 13+9 if this was a normal distribution. 4 and 22 . In our exact case, it would be 57 out of 78 stations have number of exits between 4 and 22 so 73 percent.

# How was this done
## Getting The Exits per Station
Whenever a station field is selected, there is a POST request to https://www.edl.gov.lb/feedingdata.php
The payload is in the following manner
> mode: feeders-sel2
>
> id: 2

Mode doesn't change between requests. ID is the order that of the station in the list.
`صيدا الجديدة` is 87
`الغاز ` is 1

We don't know what the ID is for each station so we need to get those.
### Get the ID for Every Station
When we look at the HTML list we notice that the each entry has an id that looks like this.
```
select2-a_substations-result-5vc4-1
```
We have the hunch that the number at the end of the ID entry is the ID that is used for the request. We tested a few and that theory seems to fit.

To get the map of IDs to stations, we need to parse the `Stations.html`. You can see how this was done through `getStationsID.py`.

The final Station and their ID numbers are in `StationIDs.csv`

Now we have the ID per station.

### Doing The requests
Now we just needs to do the request for every station. You can see how this was done with the script `getExitsPerStation.py`. The data was exported to Exit Directory.

The response for each of these requests looks like the following.
```
{
  "results": [{
    "id": "29",
    "text": "أريسكو+وادي ابو جميل"
  }, {
    "id": "1010",
    "text": "أسود"
  }, {
    "id": "25",
    "text": "باريس"
  }.....]
}

```
The next step would be to unify all of this into readable format. s
## Merging the Data into one Place
The ideal would be to merge this into one CSV. The python script that would do it is `mergeData.py`.
From this we can understand that they are 993 exits in total.

The CSV can be found in the `Data` folder. There is an excel file as well. Please note that the encoding is in UTF-8 which isn't the default for Microsoft Excel

# Getting the Cutoff Hours

The request has the following form data
This is all sent as a POST request the the url `https://www.edl.gov.lb/feedingdata.php`

```
a_substations: 20
a_feeders: 321
d1: 2021-12-27
d2: 2021-12-30
mode: load
actpre: act
```

a_substations would be the station ID. a_feeders is the exit ID
