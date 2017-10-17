from atsd_client import connect_url
from atsd_client.services import MetricsService

'''
Locate a collection of metrics that have no lastInsertDate.
'''

# Connect to an ATSD server
connection = connect_url('https://atsd_hostname:8443', 'user', 'password')

metric_service = MetricsService(connection)
# query entities without lastInsertDate
metric_list = metric_service.list(maxInsertDate="1970-01-01T00:00:00.000Z")
metrics_count = 0

print('metricName')
for metric in metric_list:
    if metric.enabled and metric.persistent \
            and metric.retentionDays == 0 and metric.seriesRetentionDays == 0:
        metrics_count += 1
        print(metric.name)

print("\nMetrics count without last insert date is %d." % metrics_count)
