# Axibase Time Series Database Client for Python

The ATSD API Client for Python simplifies the process of interacting with [Axibase Time Series Database](https://axibase.com/products/axibase-time-series-database/) through SQL and REST API.

## References

* ATSD [Data API](https://github.com/axibase/atsd-docs/tree/master/api/data#overview) documentation
* ATSD [Meta API](https://github.com/axibase/atsd-docs/tree/master/api/meta#overview) documentation
* ATSD [SQL Documentation](https://github.com/axibase/atsd-docs/tree/master/sql#overview) documentation
* [PyPI atsd_client](https://pypi.python.org/pypi/atsd_client)
* atsd_client documentation on [pythonhosted.org](http://pythonhosted.org/atsd_client)

## Requirements

Check Python version.

```sh
python -V
```

The client is supported for the following Python versions:

* Python 2.7.9 and later
* Python 3, all versions

## Installation

Install `atsd_client` module using `pip`.

```sh
pip install atsd_client
```

Alternatively, clone the repository and run the installation manually.

```sh
git clone https://github.com/axibase/atsd-api-python.git
cd atsd-api-python
python setup.py install
```

Check that the modules have been installed successfully.

```sh
python -c "import atsd_client, pandas, requests, dateutil"
```

The output will be empty if all modules are installed correctly. Otherwise, an error will be displayed showing which modules are missing.

```python
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ImportError: No module named atsd_client
```

For installation on a system without internet access, review the following [guide](offline_installation.md)

## Upgrade

Execute `pip install` command to upgrade the client to the latest version.

```sh
pip install atsd_client --upgrade --upgrade-strategy only-if-needed
```

## Usage

### Hello World

```python
  from atsd_client import connect_url

  conn = connect_url('https://atsd_hostname:8443', 'john.doe', 'password')

  response = conn.get('v1/version')
  build_info = response['buildInfo']
  print('Revision: %s ' % build_info['revisionNumber'])
```

```sh
python connect_url_check.py
```

```txt
  INFO:root:Connecting to ATSD at https://atsd_hostname:8443 as john.doe user.
  Revision: 19020
```

### Connecting to ATSD

To connect to an ATSD instance, you need to know its hostname and port, and have a user account configured on the **Admin>Users** page.

Establish a connection with the `connect_url` method.

```python
    >>> import atsd_client
    >>> conn = atsd_client.connect_url('https://atsd_hostname:8443', 'usr', 'passwd')
```

Alternatively, create a `connection.properties` file and specify its path in the `connect` method.

```ls
base_url=https://atsd_hostname:8443
username=usr
password=passwd
ssl_verify=False
```

```python
    >>> import atsd_client
    >>> conn = atsd_client.connect('/path/to/connection.properties')
```

### Initializing the Service

The client provides a set of services for interacting with a particular type of records in ATSD, for example, `Series`, `Property`, and `Message` objects as well as with metadata objects such as `Entity`, `Metric`, and `EntityGroup`. An example of creating a service is provided below.

```python
    >>> from atsd_client.services import SeriesService
    >>> svc = SeriesService(conn)
```

### Logging

Logging to stdout is enabled by default. To disable logging, add the following lines at the beginning of the script:

```python
import logging
logger = logging.getLogger()
logger.disabled = True
```

### Inserting Series Values

To insert series values into ATSD, initialize a `Series` object and populate it with timestamped values.

```python

    >>> from atsd_client.models import Sample, Series
    >>> series = Series(entity='sensor123', metric='temperature')
    >>> series.add_samples(
            Sample(value=1, time="2016-07-18T17:14:30Z"),
            Sample(value=2, time="2016-07-18T17:16:30Z")
        )
    >>> svc.insert(series)
    True
```

In addition to inserting records via `atsd_client` client, you can load datasets into ATSD by uploading CSV files or importing publicly available information from [data.gov](https://github.com/axibase/atsd-use-cases/blob/master/SocrataPython/README.md) using Axibase Collector.

### Querying Series Values

When querying series values from the database, you need to specify *entity filter*, *date filter*, and *series filter*. <br>
Forecast, Versioning, Control, and Transformation filters can also be used to filter the resulting `Series` objects.
See the [Series Query documentation](https://github.com/axibase/atsd-docs/blob/master/api/data/series/query.md) for more information.

*Series filter*: requires specifying the metric name. You can also include type, tags, and other parameters in this filter to get more specific series objects.

*Entity filter*: can be set by providing entity name, names of multiple entities, or the name of the entityGroup or entityExpression.

*Date filter*: can be set by specifying the `startDate`, `endDate`, or `interval` fields. Some **combination** of these parameters is required to establish a specific time range. The `startDate` and `endDate` fields can be provided either as keywords from [calendar syntax](https://github.com/axibase/atsd/blob/master/shared/calendar.md), an ISO 8601 formatted string, number of Unix milliseconds, or a datetime object.

Finally, to get a list of `Series` objects matching the specified filters, the `query` method of the service should be used.

```python

    >>> from atsd_client.models import SeriesQuery, SeriesFilter, EntityFilter, DateFilter
    >>> sf = SeriesFilter(metric="temperature")
    >>> ef = EntityFilter(entity="sensor123")
    >>> df = DateFilter(start_date="2016-02-22T13:37:00Z", end_date=datetime.now())
    >>> query_data = SeriesQuery(series_filter=sf, entity_filter=ef, date_filter=df)
    >>> result = svc.query(query_data)
    >>>
    >>> print(result[0]) #picking first Series object
```

```txt
    2016-07-18T17:14:30+00:00             1
    2016-07-18T17:16:30+00:00             2
    metric: temperature
    aggregate: {'type': 'DETAIL'}
    type: HISTORY
    tags: {}
    data: [<Sample v=1, t=1468862070000.0, version=None>, <Sample v=2, t=1468862190000.0, version=None>]
    entity: sensor123
```

### Exploring Results

Install the `pandas` module using pip:

```sh
pip install pandas
```

In order to access the Series object in [pandas](http://pandas.pydata.org/), a Python data analysis toolkit, utilize the built-in `to_pandas_series()` and `from_pandas_series()` methods.

```python

    >>> ts = series.to_pandas_series()
    >>> type(ts.index)
    <class 'pandas.tseries.index.DatetimeIndex'>
    >>> print(ts)
```

```txt
    2015-04-10 17:22:24.048000    11
    2015-04-10 17:23:14.893000    31
    2015-04-10 17:24:49.058000     7
    2015-04-10 17:25:15.567000    22
    2015-04-13 14:00:49.285000     9
    2015-04-13 15:00:38            3
```

### Graphing Results

To plot the series with `matplotlib`, use `plot()`:

```python
    >>> import matplotlib.pyplot as plt
    >>> series.plot()
    >>> plt.show()
```

### SQL queries

To perform SQL queries, use the `query` method implemented in the SQLService.
The returned table will be an instance of the `DataFrame` class.

```python
    >>> from atsd_client.services import SQLService
    >>> sql = SQLService(conn)
    >>> df = sql.query('select * from jvm_memory_free limit 3')
    >>> df
```

```txt
      entity                  datetime        value     tags.host
    0   atsd  2017-01-20T08:08:45.829Z  949637320.0  45D266DDE38F
    1   atsd  2017-02-02T08:19:14.850Z  875839280.0  45D266DDE38F
    2   atsd  2017-02-02T08:19:29.853Z  777757344.0  B779EDE9F45D
```

### Working with Versioned Data

Versioning enables keeping track of value changes and is described [here](https://axibase.com/products/axibase-time-series-database/data-model/versioning/).

You can enable versioning for specific metrics and add optional versioning fields to Samples using the `version` argument.

```python

    >>> from datetime import datetime
    >>> other_series = Series('sensor123', 'power')
    >>> other_series.add_samples(
                Sample(3, datetime.now(), version={"source":"TEST_SOURCE", "status":"TEST_STATUS"})
        )
```

To retrieve series values with versioning fields, add the `VersionedFilter` to the query with the `versioned` field equal to **True**.

```python

    >>> import time
    >>> from atsd_client.models import VersioningFilter
    >>> cur_unix_milliseconds = int(time.time() * 1000)
    >>> sf = SeriesFilter(metric="power")
    >>> ef = EntityFilter(entity="sensor123")
    >>> df = DateFilter(startDate="2016-02-22T13:37:00Z", endDate=cur_unix_milliseconds)
    >>> vf = VersioningFilter(versioned=True)
    >>> query_data = SeriesQuery(series_filter=sf, entity_filter=ef, date_filter=df, versioning_filter=vf)
    >>> result = svc.query(query_data)
    >>> print(result[0])
 ```

 ```txt
               time         value   version_source   version_status
    1468868125000.0           3.0      TEST_SOURCE      TEST_STATUS
    1468868140000.0           4.0      TEST_SOURCE      TEST_STATUS
    1468868189000.0           2.0      TEST_SOURCE      TEST_STATUS
    1468868308000.0           1.0      TEST_SOURCE      TEST_STATUS
    1468868364000.0          15.0      TEST_SOURCE      TEST_STATUS
    1468868462000.0          99.0      TEST_SOURCE      TEST_STATUS
    1468868483000.0          54.0      TEST_SOURCE      TEST_STATUS
```

## Examples

### Versions

|**Name**| **Description**|
|:---|:---|
|[version_check.py](examples/version_check.py) | Print out python and module versions. |

### Connection

|**Name**| **Description**|
|:---|:---|
|[connect_url_check.py](examples/connect_url_check.py) | Connect to the target ATSD instance, retrieve the database version, timezone and current time using `connect_url('https://atsd_hostname:8443', 'user', 'password')` function. |
|[connect_path_check.py](examples/connect_path_check.py) | Connect to the target ATSD instance, retrieve the database version, timezone and current time using `connect(/home/axibase/connection.properties)` function. |
|[connect_check.py](examples/connect_check.py) | Connect to the target ATSD instance, retrieve the database version, timezone and current time using `connect()` function. |

### Data Availability

|**Name**| **Description**|
|:---|:---|
|[find_broken_retention.py](examples/find_broken_retention.py)| Find series that ignore metric retention days. |
|[metrics_without_last_insert.py](examples/metrics_without_last_insert.py) | Find metrics without a last insert date. |
|[entities_without_last_insert.py](examples/entities_without_last_insert.py) | Find entities without a last insert date. |
|[find_lagging_series_for_entity_expression.py](examples/find_lagging_series_by_entity_expression.py) | Find series for matching entities that have not been updated for more than 1 day. |
|[find_lagging_series_for_entity.py](examples/find_lagging_series_by_entity.py) | Find series for the specified entity that have not been updated for more than 1 day. |
|[find_lagging_series_for_metric.py](examples/find_lagging_series_by_metric.py) | Find series for the specified metric that have not been updated for more than 1 day. |
|[find_lagging_series.py](examples/find_lagged_series.py) | Find series with last insert date lagging the maximum last insert date by more than specified grace interval.  |
|[high_cardinality_series.py](examples/high_cardinality_series.py) | Find series with too many tag combinations. |
|[high_cardinality_metrics.py](examples/high_cardinality_metrics.py) | Find metrics with series that have too many tag combinations. |
|[find_lagging_entities.py](examples/find_lagging_entities.py) | Find entities that match the specified expression filter which have stopped collecting data. |
|[find_stale_agents.py](examples/find_staling_agents.py) | Find entities that have stopped collecting data for a subset metrics.|
|[metrics_created_later_than.py](examples/metrics_created_later_than.py) | Find metrics that have been created after the specified date. |
|[entities_created_later_than.py](examples/entities_created_later_than.py) | Find entities that have been created after the specified date. |
|[find_delayed_entities.py](examples/find_delayed_entities.py) | Find entities more than n hours behind the metric's last_insert_date. |
|[series_statistics.py](examples/series_statistics.py) | Retrieve series for a given metric, for each series fetch first and last value. |
|[frequency_violate.py](examples/frequency_violate.py) | Print values that violate metric frequency. |
|[migration.py](examples/migration.py) | Compare series query responses before and after ATSD migration. |
|[data-availability.py](examples/data-availability.py) | Monitor availability of data using predefined CSV. |

### Data Manipulation

|**Name**| **Description**|
|:---|:---|
|[copy_data.py](examples/copy_data.py)| Copy data into a different period. |
|[copy_data_for_the_metric.py](examples/copy_data_for_the_metric.py) | Copy data into a new metric. |

### Record Cleanup

|**Name**| **Description**|
|:---|:---|
|[find_non-positive_values.py](examples/find_non-positive_values.py) | Find series with non-positive values for the specified metric, delete if required. |
|[delete_series_data_interval.py](examples/delete_series_data_interval.py) | Delete data for a given series with tags for the specified date interval. |
|[delete_series_for_entity_metric_tags.py](examples/delete_series_for_entity_metric_tags.py)|Delete all series for the specified entity, metric and series tags.|
|[docker_delete.py](examples/docker_delete.py)| Delete docker host entities and related container/image/network/volume entities that have not inserted data for more than 7 days. |
|[entities_expression_delete.py](examples/entities_expression_delete.py)| Delete entities that match the specified expression filter. |
|[delete_entity_tags.py](examples/delete_entity_tags.py)| Delete specific entity tags from entities that match an expression. |
|[delete_entity_tags_starting_with_expr.py](examples/delete_entity_tags_starting_with_expr.py)| Delete entity tags started with expression. |
|[update_entity_tags_from_property.py](examples/update_entity_tags_from_property.py)| Update entity tags from the corresponding property tags. |

### Reporting

|**Name**| **Description**|
|:---|:---|
|[entity_print_metrics_html.py](examples/entity_print_metrics_html.py) | Print metrics for entity into HTML or ASCII table. |
|[export_messages.py](examples/export_messages.py) | Export messages into CSV. |

> Note that some of the examples above use the `prettytable` module to format displayed records. The module can be installed as follows:

```sh
pip install prettytable
# or
pip install https://pypi.python.org/packages/source/P/PrettyTable/prettytable-0.7.2.tar.gz
```
