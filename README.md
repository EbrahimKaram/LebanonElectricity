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

Now we need to get the cutoff times. Let's get the data of the past two weeks and try to convert the response into an hourly CSV.

We will export the data of each exit into `Cutoff Times`.

Sometimes you will get null responses that just throws a row of nulls.
`dateoffeeding` would be set to null in this case.

The response would look as such

```
{
  "status": true,
  "list_feeders": [{
    "substationid": "18",
    "substationname": "بكفيا",
    "s_type": "OUT",
    "kadesha": "N",
    "s_rank": "0",
    "fid": "305",
    "feedername": "بسكنتا",
    "subgroup": "B1",
    "excepted": "0",
    "f_type": "OUT   ",
    "f_rank": "0",
    "id": "3661152",
    "dateoffeeding": "2021-12-20",
    "feederid": "305",
    "time0": "0",
    ......
    "time22": "0",
    "time23": "0",
    "user_id": "13"
  },....
  ]
}
```


## Making the Data hourly instead of daily
The data is a bit to wide.
https://pandas.pydata.org/docs/reference/api/pandas.wide_to_long.html
We want the hour data to be its own entry so we can do temporal Analysis easier.
Check for `getCutoffTimes.py` to see how this works.

Now there is a lot of data that comes back. I'm gonna remove the data that seems redundant. I converted the response into a dataframe and I'm gonna remove the data that seems useless.

```
for column in df2.columns:
    print(column,df2[column].unique())
```
We had 39 columns now we only have 9.


# ForeCasting

I had chat GPT and Gemini work on this. 

Chat GPT gave the initial algorithm but gemini made something faster and it is what I ended up using. 

# Website

This was a Chat GPT code that helped do this

# TODO and other Tasks
## Reading up on Time Series Classification
Time Series Classification
We have time data.

https://towardsdatascience.com/a-brief-introduction-to-time-series-classification-algorithms-7b4284d31b97
Read the article above and see if we can forecast cutoffs
We might just use Facebook prophet.
Ideas are coming from this Facebook Post
https://www.facebook.com/groups/DevCBeirut/permalink/4630462727071047/
hour-by-hour binary classification

There's a forecaster online
https://forecastr-io.herokuapp.com/

We might need to use sktime but we need to convert time into an hour by hour data.

The most popular approach might be RISE which is what prophet is. (prophet is the open source porject from facebook)

https://www.sktime.org/en/latest/examples/rocket.html
It seems the best naïve approach is to use prophet in our case since I really presume there is a frequency here. The article at first recommends rocket if we really don't know anything.

### Our Scenario
We presume that cutoffs have a kind of periodicity. It's not entirely random. In a raw Fourier Analysis, there should be some kind of frequency to the readings.

We are doing binary classification on the time series data. There is electricity or there is not. Since we only have two outcomes or two classes, this called binary classification.

Now on every day there are 24 readings. In order to benefit from the periodicity of the data we need to convert 24 columns into 24 rows. It will make the model a bit more scalable. It would allows us to memorize less data.

## Binary Time Series Forecasting
Facebook prophet won't work with binary or distinct outputs. We might need to use some statmodels.

Now Facebook prophet uses Stan which is used for Bayesian modeling.
