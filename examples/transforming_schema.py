# Create client for old-schema client

from io import StringIO

import pandas

from atsd_client import connect
from atsd_client.services import SQLService, CommandsService

# Connect to source ATSD

# source_db_connection = connect_url('https://atsd_hostname:8443', 'username', 'password')
source_db_connection = connect('/path/to/source.connection.properties')
source_sql_service = SQLService(source_db_connection)

# target_db_connection = connect_url('https://atsd_hostname:8443', 'username', 'password')
target_db_connection = connect('/path/to/target.connection.properties')
target_command_service = CommandsService(target_db_connection)

metric_name = 'metric_name'
sql_query = 'SELECT entity,metric, value, text, datetime, tags.* FROM "' + metric_name + '"'
# print sql_query

keys_to_remove = ["time_zone"]
values_to_remove = ['false']
default_tags_to_remove = {
    '_index': '1',
    'status': '0'
}
batch_size = 2
transformed_commands_batch = []

# read df from response with string dtype
response = source_sql_service.query_with_params(sql_query)
df = pandas.read_csv(StringIO(response), dtype=str, sep=',')

for index, row in df.where(pandas.notnull(df), None).iterrows():
    row_dict = row.to_dict()
    # transforming
    """
    * Swap entity and metric
    * Discard tags that contain false values
    * Discard time_zone tag
    * Discard _index tag if it is equal 1
    * Discard status tag if it is equal 0
    """

    # stores fixed series fields
    series = {k: v for k, v in row_dict.iteritems()
              if not k.startswith('tags.')}
    # stores series tags
    tags = dict(map(lambda kv: (kv[0].replace("tags.", ""), kv[1]),
                    {k: v for k, v in row_dict.iteritems() if k.startswith('tags.')}.iteritems()))

    filter_tags = {k: v for k, v in tags.iteritems()
                   if not (k in keys_to_remove or
                           v in values_to_remove or
                           (default_tags_to_remove.has_key(k) and default_tags_to_remove[k] == v))}

    # Generate command to insert in new db
    command = 'series e:{entity} {value_part} {text_part} d:{datetime} {tags}'.format(
        entity=series['metric'],
        value_part='m:' + series['entity'] + '=' + str(series['value']) if series['value'] is not None else "",
        text_part='x:' + series['entity'] + '=' + series['text'] if series['text'] is not None else "",
        datetime=series['datetime'],
        tags="".join(map(lambda x: ' t:' + x + '=' + str(tags[x]), filter_tags.keys()))
    )
    # if reach batch size send commands
    if len(transformed_commands_batch) == batch_size:
        for command in transformed_commands_batch:
            print(command)
        transformed_commands_batch = [command]
    else:
        transformed_commands_batch.append(command)
        # target_command_service.send_commands(transformed_commands_batch)

if len(transformed_commands_batch) > 0:
    for command in transformed_commands_batch:
        print(command)

# target_command_service.send_commands(transformed_commands)
