from atsd_client import connect_url
from atsd_client.services import MetricsService

'''
Locate metrics with high-cardinality series that have tags more than specified cardinality.
Output metric name and maximum number of tags combinations.
'''

# Connect to an ATSD server
connection = connect_url('https://atsd_hostname:8443', 'user', 'password')

metrics_service = MetricsService(connection)

# query all metrics that have lastInsertDate, i.e. series
metrics = metrics_service.list(minInsertDate="1970-01-01T00:00:00.000")

# set cardinality
cardinality = 10
metric_count = 0

print('metric, maximum number of tags')
for metric in metrics:
    # query series list for each metric
    series_list = metrics_service.series(metric)
    max_tags = -1
    for s in series_list:
        # check tags cardinality for each series in list
        tags_count = len(s.tags)
        if tags_count > cardinality and tags_count > max_tags:
            max_tags = tags_count
    if max_tags > -1:
        metric_count += 1
        print('%s, %d' % (metric.name, max_tags))

print("Number of metrics that have more than %d tags combinations is %d " % (cardinality, metric_count))
