from atsd_client import connect, connect_url
from atsd_client.services import MetricsService

'''
Locate a collection of metrics that have been created after specified date.
'''

# Connect to ATSD server
#connection = connect('/path/to/connection.properties')
connection = connect_url('https://atsd_hostname:8443', 'username', 'password')

# Initialize services
metrics_service = MetricsService(connection)
# query all metrics created after specified_date
metric_list = metrics_service.list(expression="createdDate > '2018-05-16T00:00:00Z'")

print('metric_name')
for metric in metric_list:
    print(metric.name)

