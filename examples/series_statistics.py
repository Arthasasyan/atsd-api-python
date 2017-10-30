from datetime import datetime

from atsd_client import connect_url
from atsd_client.models import SeriesQuery, SeriesFilter, EntityFilter, DateFilter, ControlFilter
from atsd_client.services import MetricsService, SeriesService

'''
Retrieve series for a given metric, for each series fetch first and last value with corresponding dates.
'''

# Connect to an ATSD server
connection = connect_url('https://atsd_hostname:8443', 'user', 'password')

svc = SeriesService(connection)
metric_service = MetricsService(connection)

# set metric name
metric_name = "ca.daily.reservoir_storage_af"

# print header
print('entity, entityLabel, seriesTags, firstValueDate, firstValue, lastValueDate, lastValue')

# query series with current metric for all entities with meta information in ascending order to get first value
sf = SeriesFilter(metric=metric_name)
ef = EntityFilter(entity='*')
df = DateFilter(startDate="1970-01-01T00:00:00Z", endDate=datetime.now())
cf = ControlFilter(limit=1, addMeta=True, direction="ASC")
query = SeriesQuery(series_filter=sf, entity_filter=ef, date_filter=df, control_filter=cf)
series_list_asc = svc.query(query)

# change filter to get last value and query series, descending order set by default
query = SeriesQuery(series_filter=sf, entity_filter=ef, date_filter=df, control_filter=ControlFilter(limit=1))
series_list_desc = svc.query(query)

for series_asc in series_list_asc:
    if len(series_asc.data) > 0:

        # get corresponding descending series and remove it from desc list
        index_series_desc = series_list_desc.index(series_asc)
        series_desc = series_list_desc.pop(index_series_desc)

        # get label from meta information
        label = series_asc.meta['entity'].label if series_asc.meta['entity'].label is not None else ''
        # get first and last samples in series to output
        print('%s, %s, %s, %s, %s, %s, %s' % (series_asc.entity, label, series_asc.get_tags(),
                                              series_asc.get_first_value_date(), series_asc.get_first_value(),
                                              series_desc.get_first_value_date(), series_desc.get_first_value()))

# print remaining series that are not in ascending list
for series_desc in series_list_desc:
    label = series_desc.meta['entity'].label if series_desc.meta['entity'].label is not None else ''
    print('%s, %s, %s, %s, %s, %s, %s' % (series_desc.entity, label, series_desc.get_tags(),
                                          '', '',
                                          series_desc.get_first_value_date(), series_desc.get_first_value()))
