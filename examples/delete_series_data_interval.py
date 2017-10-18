from atsd_client import connect_url
from atsd_client.models import SeriesFilter, EntityFilter, DateFilter, SeriesQuery
from atsd_client.services import SeriesService

'''
Delete data for a given series with tags for the specified date interval.
'''

# Connect to an ATSD server
connection = connect_url('https://atsd_hostname:8443', 'user', 'password')

# set series
metric = 'm-to-delete'
entity = 'e-to-delete'
tags = {'tag_key_1': 'tag_value_1', 'tag_key_2': 'tag_value_2'}

# specify date interval
startDate = "2017-10-01T00:00:00Z"
endDate = "2017-10-02T00:00:00Z"

series_service = SeriesService(connection)

# query the series to be deleted, use exactMatch to exclude not specified tags
sf = SeriesFilter(metric=metric, tags=tags, exactMatch=True)
ef = EntityFilter(entity=entity)
df = DateFilter(startDate=startDate, endDate=endDate)
query = SeriesQuery(series_filter=sf, entity_filter=ef, date_filter=df)
series_list = series_service.query(query)

if len(series_list) > 1:
    raise Exception('There are multiple series meet the requirements')

series = series_list[0]

# check data existence
if len(series.data) == 0:
    print('No data in required interval')
else:
    # replace value of samples with nan
    for sample in series.data:
        sample.v = None
    series.aggregate = None
    series_service.insert(series)
