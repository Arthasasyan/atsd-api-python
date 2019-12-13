import logging
import argparse
from atsd_client import connect
from atsd_client.services import SeriesService, EntitiesService, MetricsService
from atsd_client.models import SeriesQuery, SeriesFilter, EntityFilter, DateFilter


def no_data(series_list):
    return len(series_list[0].data) == 0


def get_series_with_tags(series_list, tags):
    for series in series_list:
        if series.tags == tags:
            return series
    return None


#Parse CLI args
parser = argparse.ArgumentParser(description="Copy metric values for series with source entity to one with"
                                             "destination entity")
parser.add_argument('--tag_expression', '-te', required=False, help='Tag expression to match source series')
parser.add_argument('--dry_run', '-dr', required=False, help='Run script without sending series to ATSD',
                    action='store_const', const=True)
requiredArguments = parser.add_argument_group('required arguments')
requiredArguments.add_argument('--src_entity', '-se', required=True, help='Source entity')
requiredArguments.add_argument('--dst_entity', '-de', required=True, help='Destination entity')
requiredArguments.add_argument('--metric_name', '-mn', required=True, help='Metric to be cloned')
args = parser.parse_args()
source_entity = args.src_entity
dst_entity = args.dst_entity
metric = args.metric_name
tag_expression = None
if args.tag_expression is not None:
    tag_expression = args.tag_expression
start_date = '1970-01-01T00:00:00Z'
dry_run = False
if args.dry_run is not None:
    dry_run = True


connection = connect('./connection.properties')

entity_service = EntitiesService(connection)

if entity_service.get(source_entity) is None:
    print("'" + source_entity + "' entity does not exist")
    exit(1)

if entity_service.get(dst_entity) is None:
    print("'" + dst_entity + "' entity does not exist")
    exit(1)

metric_service = MetricsService(connection)

if metric_service.get(metric) is None:
    print("'" + metric + "' metric does not exist")
    exit(1)

series_service = SeriesService(connection)

dst_entity_filter = EntityFilter(dst_entity)
dst_date_filter = DateFilter(start_date, 'now')
series_filter = SeriesFilter(metric, tag_expression=tag_expression)
dst_series_query = SeriesQuery(series_filter, dst_entity_filter, dst_date_filter)
dst_series = series_service.query(dst_series_query)

if no_data(dst_series):
    print('No destination series found for these parameters')
    exit(1)


def err(tags, time):
    return ("No series found for '" + source_entity + "' entity, '" + metric + "' metric and '" +
          str(tags) + "' tags before " + time)


source_entity_filter = EntityFilter(source_entity)
for series in dst_series:
    first_dst_time = series.times()[0]  # get first time from sorted collection
    source_date_filter = DateFilter(start_date, first_dst_time)
    source_series_filter = SeriesFilter(metric, series.tags)
    source_query = SeriesQuery(source_series_filter, source_entity_filter, source_date_filter)
    source_series = series_service.query(source_query)

    if no_data(source_series):
        logging.info(err(series.tags, first_dst_time))
        continue

    target_series = get_series_with_tags(source_series, series.tags)

    if target_series is None:
        logging.info(err(series.tags, first_dst_time))
        continue

    target_series.entity = dst_entity
    if not dry_run:
        series_service.insert(target_series)

    logging.info("Sent series with '%s' entity, '%s' metric, '%s' tags" % (target_series.entity,
                                                                          target_series.metric, target_series.tags))
    for sample in target_series.data:
        logging.info("Sample: %s : %d " % (sample.get_date(), sample.v))

