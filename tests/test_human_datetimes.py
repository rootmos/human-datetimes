import datetime
import unittest
import zoneinfo

import pytest
from parameterized import parameterized

from . import iso8601, fresh

from human_datetimes import parse
from human_datetimes.utils import figure_out_countrycode_from_timezone

class ParseHumanDatetimes(fresh.Seed, unittest.TestCase):
    @parameterized.expand([
        ("23 January 2025", "Europe/Stockholm", "2025-01-23T00:00:00+01:00"),
        ("6 juni 1979", "Europe/Stockholm", "1979-06-06T00:00:00+01:00"),
        ("6 juni 1980", "Europe/Stockholm", "1980-06-06T00:00:00+02:00"),
        ("6 June 1979", "Europe/Stockholm", "1979-06-06T00:00:00+01:00"),
        ("6 June 1980", "Europe/Stockholm", "1980-06-06T00:00:00+02:00"),
        ("1981-02-03 17:21", "Europe/Stockholm", "1981-02-03T17:21:00+01:00"),
        ("1981-07-03 17:21", "Europe/Stockholm", "1981-07-03T17:21:00+02:00"),
        ("23/1 2025", "US/Eastern", "2025-01-23T00:00:00-05:00"),
        ("noon 7th June 1902", "US/Eastern", "1902-06-07T12:00:00-05:00"),
        ("1999-11-13 midnight", "EET", "1999-11-13T00:00:00+02:00"),
    ])
    def test_absolute(self, human_string, tz, expected):
        actual = parse(human_string=human_string, tz=tz)
        assert iso8601(actual) == expected

    @parameterized.expand([
        ("foo", "local"),
        ("tomorrow", "foo"),
    ])
    def test_invalid(self, human_string, tz):
        with self.assertRaises(Exception):
            print(parse(human_string=human_string, tz=tz))

    @parameterized.expand([
        ("tomorrow", "UTC", "2025-01-23T16:38:46+01:00", "2025-01-24T15:38:46+00:00"),
        ("monday", "UTC", "1970-01-01T00:00:00+00:00", "1970-01-05T00:00:00+00:00"),
        ("February", "UTC", "1970-01-01T00:00:00+00:00", "1970-02-01T00:00:00+00:00"),
        ("16/7", "UTC", "1970-01-01T00:00:00+00:00", "1970-07-16T00:00:00+00:00"),
        ("16/7", "UTC", "1970-08-01T00:00:00+00:00", "1971-07-16T00:00:00+00:00"),
        ("today 16:40", "UTC", "1970-01-01T00:00:00+00:00", "1970-01-01T16:40:00+00:00"),
        ("today 16:40", "UTC", "1970-01-01T17:00:00+00:00", "1970-01-01T16:40:00+00:00"),
        ("16:40", "UTC", "1970-01-01T00:00:00+00:00", "1970-01-01T16:40:00+00:00"),
        ("16:40", "UTC", "1970-01-01T17:00:00+00:00", "1970-01-02T16:40:00+00:00"),
        ("07:00 16 July", "Europe/Stockholm", "1981-01-01T00:00:00+00:00", "1981-07-16T07:00:00+02:00"),
        ("today 16:40", "Europe/Stockholm", "1970-01-01T00:00:00+00:00", "1970-01-01T16:40:00+01:00"),
        ("16:40", "Europe/Stockholm", "1970-01-01T00:00:00+00:00", "1970-01-01T16:40:00+01:00"),
        ("16:40", "Europe/Stockholm", "1981-07-01T00:00:00+00:00", "1981-07-01T16:40:00+02:00"),
        ("Friday 10:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-21T10:00:00+01:00"),
        ("fredag 10:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-21T10:00:00+01:00"),
        ("Friday 7:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-28T07:00:00+01:00"),
        ("fredag 7:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-28T07:00:00+01:00"),
        ("05:58", "Europe/Stockholm", "2025-03-31T06:19:40+00:00", "2025-04-01T05:58:00+02:00"),
        ("07:00", "UTC", "2025-03-31T06:00:00+00:00", "2025-03-31T07:00:00+00:00"),
        ("05:00", "UTC", "2025-03-31T06:00:00+00:00", "2025-04-01T05:00:00+00:00"),
    ])
    def test_relative(self, human_string, tz, now, expected):
        actual = parse(human_string=human_string, tz=tz, now=iso8601(now))
        assert iso8601(actual) == expected

    @pytest.mark.skip
    def test_local(self):
        tz = "Europe/Helsinki"
        now = datetime.datetime.now(tz=zoneinfo.ZoneInfo(tz))
        target = now + datetime.timedelta(hours=2)
        target = target.replace(minute=0, second=0, microsecond=0)
        s = f"{target.hour}:00"
        actual = parse(human_string=s, tz=tz)
        assert iso8601(actual) == iso8601(target)

    @parameterized.expand([
        ("*/10 * * * *", "UTC", "1970-01-01T00:01:00+00:00", "1970-01-01T00:10:00+00:00"),
        ("* * * * 7", "UTC", "1970-01-01T00:01:00+00:00", "1970-01-04T00:00:00+00:00"),
        ("* * * 3 0", "UTC", "1970-01-01T00:01:00+00:00", "1970-03-01T00:00:00+00:00"),
        ("* * 1 6 *", "Europe/Stockholm", "1981-01-01T00:00:00+00:00", "1981-06-01T00:00:00+02:00"),
        ("* * 1 6 *", "Europe/Stockholm", "1981-05-29T00:00:00+00:00", "1981-06-01T00:00:00+02:00"),
        ("* * 1 6 *", "Europe/Stockholm", "1981-01-01T00:00:00+00:00", "1981-06-01T00:00:00+02:00"),
    ])
    def test_cron(self, human_string, tz, now, expected):
        actual = parse(human_string=human_string, tz=tz, now=iso8601(now))
        assert iso8601(actual) == expected

    def test_datetime_iso8601_roundtrip(self):
        for _ in range(100):
            dt = fresh.datetime()
            assert parse(human_string=dt.isoformat(), now=fresh.datetime()) == dt

class TimezoneRoundtrip(unittest.TestCase):
    @parameterized.expand([
        ("UTC"),
        # ("UTC+7"),
        # ("+07:00"),
        ("EET"),
        ("Europe/Stockholm"),
        ("CET"),
        # ("CEST"),
    ])
    def test_timezone_roundtrip(self, tz):
        tzinfo = zoneinfo.ZoneInfo(tz)
        assert str(tzinfo) == tz

class TimezoneBusinessDay(unittest.TestCase):
    @parameterized.expand([
        ("sista arbetsdagen innan 1 dec 16:28", "Europe/Stockholm", None, "2025-03-11T08:00:00+01:00", "2025-11-28T16:28:00+01:00"),
    ])
    def test_business_day(self, human_string, tz, country, now, expected):
        actual = parse(human_string=human_string, tz=tz, country=country, now=iso8601(now))
        assert iso8601(actual) == expected

class TimezoneTimezoneAndCountry(unittest.TestCase):
    @parameterized.expand([
        ("Europe/Stockholm", "SE"),
        ("America/New_York", "US"),
    ])
    def test_country_from_timezone(self, tz, country):
        assert figure_out_countrycode_from_timezone(tz) == country
