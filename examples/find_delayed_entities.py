import sys
from datetime import timedelta

from atsd_client import connect_url
from atsd_client.services import MetricsService, EntitiesService

'''
Find series with last_insert_date more than n hours behind the metric's last_insert_date.
Print entities of that the series.
'''

# Connect to an ATSD server
connection = connect_url('https://atsd_hostname:8443', 'user', 'password')

# specify metric name
metric_name = "ca.reservoir_storage_af"

# set grace interval in hours
grace_interval_hours = 24 * 7

entities_service = EntitiesService(connection)
metrics_service = MetricsService(connection)

# query required metric meta data
metric = metrics_service.get(metric_name)
if metric is None:
    print('No metric with name %s' % metric_name)
    sys.exit()
elif metric.last_insert_date is None:
    print('No data for metric name %s' % metric_name)
    sys.exit()

# calculate the upper boundary for the allowed last_insert_date values excluding grace interval
max_insert_date = metric.last_insert_date - timedelta(seconds=grace_interval_hours * 3600)

# query series list for the metric
series_list = metrics_service.series(metric, min_insert_date="2017-09-01T00:00:00.000Z", max_insert_date=max_insert_date)

# make dictionary from entity and last_insert_date, store maximum value of last_insert_date
various_entities = dict()
for series in series_list:
    last_insert_date = various_entities.get(series.entity)
    if last_insert_date is None or last_insert_date < series.last_insert_date:
        various_entities[series.entity] = series.last_insert_date

print('entity_name,entity_label,last_insert_date')
for entity in various_entities:
    label = entities_service.get(entity).label
    last_insert_date = various_entities[entity]
    print('%s,%s,%s' % (entity, label if label is not None else '', last_insert_date))
