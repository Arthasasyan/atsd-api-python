"""
Copyright 2015 Axibase Corporation or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License").
You may not use this file except in compliance with the License.
A copy of the License is located at

https://www.axibase.com/atsd/axibase-apache-2.0.pdf

or in the "license" file accompanying this file. This file is distributed
on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied. See the License for the specific language governing
permissions and limitations under the License.
"""


import time
from datetime import datetime, timedelta
import numbers
import copy
from .._jsonutil import Serializable


def _strp(time_str):
    """
    :param time_str: in format '%Y-%m-%dT%H:%M:%SZ%z'
    :return: timestamp in milliseconds
    """
    t, tz = time_str.split('Z')

    t = time.strptime(t, '%Y-%m-%dT%H:%M:%S')

    sig, hour, min = tz[0], tz[1:3], tz[3:5]

    tz_offset = int(sig + hour) * 60 * 60 + int(sig + min) * 60
    loc_offset = time.timezone
    offset = loc_offset - tz_offset

    timestamp = int((time.mktime(t) + offset) * 1000)

    return timestamp


def to_posix_timestamp(dt):
    offset = dt.utcoffset() if dt.utcoffset() is not None else timedelta(seconds=-time.timezone)
    utc_naive = dt.replace(tzinfo=None) - offset
    return int((utc_naive - datetime(1970, 1, 1)).total_seconds() * 1000)


# class _Version(Serializable):
#
#     def __init__(self, source=None, status=None, time=None):
#         #: `str`
#         self.source = source
#         #: `str`
#         self.status = status
#         #: `int` millis
#         self.time = time
#
#     def __str__(self):
#         res = []
#         if self.source is not None:
#             res.append('source=' + self.source)
#         if self.status is not None:
#             res.append('status=' + self.status)
#         if self.time is not None:
#             res.append('time=' + str(self.time))
#         return '\t'.join(res)


class Property(Serializable):
    def __init__(self, type, entity, tags,
                 key=None,
                 timestamp=None):
        #: `str` property type name
        self.type = type
        #: `str` entity name
        self.entity = entity
        #: `dict` containing object keys
        self.tags = tags

        #: `dict` of ``name: value`` pairs that uniquely identify
        #: the property record
        self.key = key
        #: time in Unix milliseconds
        self.timestamp = timestamp


class Series(Serializable):
    def __init__(self, entity, metric, data=None, tags=None):
        #: `str` entity name
        self.entity = entity
        #: `str` metric name
        self.metric = metric

        # an list of {'t': time, 'v': value} objects
        # use add value instead
        self._data = []
        if data is not None:
            for sample in data:
                sample_copy = copy.deepcopy(sample)
                if sample_copy['v'] == 'NaN':
                    sample_copy['v'] = float('nan')
                self._data.append(sample_copy)

        #: `dict` of ``tag_name: tag_value`` pairs
        self.tags = tags

    def __str__(self):

        if len(self._data) > 20:
            disp_data = self._data[:10] + self._data[-10:]
        else:
            disp_data = self._data

        rows = []
        for sample in disp_data:
            if 'version' in sample:
                rows.append('{t}\t{v}\t{version}'.format(**sample))
            else:
                rows.append('{t}\t{v}'.format(**sample))

        if len(self._data) > 20:
            res = '\n'.join(rows[:10]) + '\n...\n' + '\n'.join(rows[10:])
        else:
            res = '\n'.join(rows)

        for key in self.__dict__:
            if not key.startswith('_'):
                res += '\n{0}: {1}'.format(key, getattr(self, key))

        return res

    @staticmethod
    def from_pandas_series(entity, metric, ts):
        """
        :param entity: str entity name
        :param metric: str metric name
        :param ts: pandas time series object
        :return: :class:`.Series` with data from pandas time series
        """
        res = Series(entity, metric)
        for dt in ts.index:
            res.add_value(ts[dt], dt)

        return res

    @property
    def data(self):
        """data getter, use ``add_value()`` method to set values

        :return: an array of {'t': time, 'v': value} objects
        """
        return self._data

    def add_value(self, v, t=None, version=None):
        """add time-value pair to series
        time could be specified as `int` in milliseconds, as `str` in format
        ``%Y-%m-%dT%H:%M:%SZ%z`` (e.g. 2015-04-14T07:03:31Z), as `datetime`

        :param version:
        :param v: value number
        :param t: `int` | `str` | :class: `.datetime` (default t = current time)
        """
        if t is None:
            t = int(time.time() * 1000)

        if isinstance(t, str):
            t = _strp(t)
        if isinstance(t, datetime):
            t = to_posix_timestamp(t)
        if not isinstance(t, numbers.Number):
            raise ValueError('data "t" should be either number or str')

        if version is None:
            sample = {'v': v, 't': t}
        else:
            sample = {'v': v, 't': t, 'version': version}

        self._data.append(sample)

    def values(self):
        """valid versions of series values
        :return: [`Number`]
        """

        res = []
        for num, sample in enumerate(self._data):
            if num > 0 and sample['t'] == self._data[num - 1]['t']:
                res[-1] = sample['v']
            else:
                res.append(sample['v'])

        return res

    def times(self):
        """valid versions of series times in seconds
        :return: [`float`]
        """

        res = []
        for num, sample in enumerate(self._data):
            if num > 0 and sample['t'] == self._data[num - 1]['t']:
                res[-1] = datetime.fromtimestamp(sample['t'] * 0.001)
            else:
                res.append(datetime.fromtimestamp(sample['t'] * 0.001))

        return res

    def to_pandas_series(self):
        """
        :return: pandas time series object
        """
        import pandas as pd

        return pd.Series(self.values(), index=self.times())

    def plot(self):
        """
        plot series in matplotlib.pyplot
        """
        try:
            return self.to_pandas_series().plot()
        except ImportError:
            import matplotlib.pyplot as plt

            return plt.plot(self.times(), self.values())


class Alert(Serializable):
    def __init__(self, id,
                 rule=None,
                 entity=None,
                 metric=None,
                 lastEventTime=None,
                 openTime=None,
                 value=None,
                 message=None,
                 tags=None,
                 textValue=None,
                 severity=None,
                 repeatCount=None,
                 acknowledged=None,
                 openValue=None):
        self.id = id

        #: `str`
        self.rule = rule
        #: `str`
        self.entity = entity
        #: `str`
        self.metric = metric
        #: `long`
        self.lastEventTime = lastEventTime
        #: `long`
        self.openTime = openTime
        #: `Number`
        self.value = value
        self.message = message
        #: `dict`
        self.tags = tags
        #: `str`
        self.textValue = textValue
        #: :class:`.Severity`
        self.severity = severity
        #: `int`
        self.repeatCount = repeatCount
        #: `bool`
        self.acknowledged = acknowledged
        #: `Number`
        self.openValue = openValue


class AlertHistory(Serializable):
    def __init__(self,
                 alert=None,
                 alertDuration=None,
                 alertOpenTime=None,
                 entity=None,
                 metric=None,
                 receivedTime=None,
                 repeatCount=None,
                 rule=None,
                 ruleExpression=None,
                 ruleFilter=None,
                 schedule=None,
                 severity=None,
                 tags=None,
                 time=None,
                 type=None,
                 value=None,
                 window=None):
        self.alert = alert
        #: `number`
        self.alertDuration = alertDuration
        #: `long` milliseconds
        self.alertOpenTime = alertOpenTime
        #: `str`
        self.entity = entity
        #: `str`
        self.metric = metric
        #: `long` milliseconds
        self.receivedTime = receivedTime
        self.repeatCount = repeatCount
        self.rule = rule
        #: `str`
        self.ruleExpression = ruleExpression
        self.ruleFilter = ruleFilter
        self.schedule = schedule
        self.severity = severity
        #: `dict`
        self.tags = tags
        #: `long` milliseconds
        self.time = time
        self.type = type
        #: `Number`
        self.value = value
        self.window = window

# if __name__ == '__main__':
#     import pandas as pd
#     now = int(time.time() * 1000)
#     dt = datetime.fromtimestamp(now * 0.001)
#     print now, dt, _to_posix_timestamp(dt)
#
#     ts = pd.Series([1], index=[datetime.fromtimestamp(now * 0.001)])
#
#     res = _to_posix_timestamp(ts.index[0])
#     dt = datetime.fromtimestamp(res * 0.001)
#
#     print res, dt