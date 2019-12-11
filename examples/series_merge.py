import argparse
from atsd_client import connect
from atsd_client.services import SeriesService, EntitiesService, MetricsService
from atsd_client.models import SeriesQuery, SeriesFilter, EntityFilter, DateFilter, Series
from atsd_client._time_utilities import to_milliseconds


def no_data(series_list):
    return len(series_list[0].data) == 0


def get_series_with_tags(series_list, tags):
    for series in series_list:
        if series.tags == tags:
            return series
    return None


#Parse CLI args
parser = argparse.ArgumentParser()
parser.add_argument('--src_entity', nargs=1, required=True, help='Source entity')
parser.add_argument('--dst_entity', nargs=1, required=True, help='Destination entity')
parser.add_argument('--metric_name', nargs=1, required=True, help='Metric to be cloned')
parser.add_argument('--tag_expression', nargs=1, required=False, help='Tag expression to be acquired for source series')
parser.add_argument('--start_date', nargs=1, required=True, help='Start date to retrieve source series')
parser.add_argument('--end_date', nargs=1, required=True, help='End date to retrieve destination series')
args = parser.parse_args()
source_entity = args.src_entity[0]
dst_entity = args.dst_entity[0]
metric = args.metric_name[0]
tag_expression = None
if args.tag_expression is not None:
    tag_expression = args.tag_expression[0]
start_date = args.start_date[0]
end_date = args.end_date[0]


connection = connect('./connection.properties')

entity_service = EntitiesService(connection)

if entity_service.get(source_entity) is None:
    raise NameError("'" + source_entity + "' entity does not exist")

if entity_service.get(dst_entity) is None:
    raise NameError("'" + dst_entity + "' entity does not exist")

metric_service = MetricsService(connection)

if metric_service.get(metric) is None:
    raise NameError("'" + metric + "' metric does not exist")


series_service = SeriesService(connection)
series_filter = SeriesFilter(metric, tag_expression=tag_expression)
source_entity_filter = EntityFilter(source_entity)
source_date_filter = DateFilter(start_date, end_date)
source_query = SeriesQuery(series_filter, source_entity_filter, source_date_filter)
source_series = series_service.query(source_query)

if no_data(source_series):
    print('No source series found for these parameters')
    exit(1)


def err(tags):
    return ("No series found for '" + dst_entity + "' entity, '" + metric + "' metric and '" +
          str(tags) + "' tags")


print(len(source_series))
dst_entity_filter = EntityFilter(dst_entity)
for series in source_series:
    dst_series_filter = SeriesFilter(metric, series.tags)
    dst_series_query = SeriesQuery(dst_series_filter, dst_entity_filter, source_date_filter)
    dst_series = series_service.query(dst_series_query)
    if no_data(dst_series):
        print(err(series.tags))
        continue
    target_series = get_series_with_tags(dst_series, series.tags)
    if target_series is None:
        print(err(series.tags))
        continue
    series.sort()
    first_time = to_milliseconds(target_series.times()[0])  # get first time from sorted collection
    samples = []
    for sample in series.data:
        if sample.t > first_time:
            break
        samples.append(sample)

    if len(samples) == 0:
        print(err(series.tags) + " before " + str(first_time))
    series_to_insert = Series(dst_entity, metric, samples, series.tags)
    series_service.insert(series_to_insert)
