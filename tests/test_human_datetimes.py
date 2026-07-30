from datetime import datetime, timedelta
import unittest
import zoneinfo

from . import fresh

from human_datetimes import parse
from human_datetimes.utils import figure_out_countrycode_from_timezone

import pytest
from parameterized import parameterized

def iso8601(x: str | None) -> datetime | None:
    if x is None:
        return None
    return datetime.fromisoformat(x)

class AssertDatetimeEqual:
    @staticmethod
    def prepareDatetime(x: str | datetime) -> tuple[str, datetime]:
        if isinstance(x, str):
            xs, xt = x, iso8601(x)
            assert xt is not None
        else:
            xs, xt = x.isoformat(timespec="seconds"), x
            assert xs is not None
        return xs, xt

    def assertDatetimeEqual(self, x: str | datetime, y: str | datetime, strict=True):
        xs, xt = self.prepareDatetime(x)
        ys, yt = self.prepareDatetime(y)

        assert xs == ys
        if strict:
            assert xt == yt

    def assertDatetimeNotEqual(self, x: str | datetime, y: str | datetime, strict=True):
        xs, xt = self.prepareDatetime(x)
        ys, yt = self.prepareDatetime(y)

        assert xs != ys
        if strict:
            assert xt != yt

class ParseHumanDatetimes(fresh.Seed, AssertDatetimeEqual, unittest.TestCase):
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
        self.assertDatetimeEqual(actual, expected)

    @parameterized.expand([
        ("foo", "local"),
        ("tomorrow", "foo"),
    ])
    def test_invalid(self, human_string, tz):
        with self.assertRaises(Exception):
            print(parse(human_string=human_string, tz=tz))

    @parameterized.expand([
        ("tomorrow", "UTC", "2025-01-23T16:38:46+01:00", "2025-01-24T15:38:46+00:00"),
        ("yesterday", "UTC", "2025-01-23T16:38:46+01:00", "2025-01-22T15:38:46+00:00"),
        ("monday", "UTC", "1970-01-01T00:00:00+00:00", "1970-01-05T00:00:00+00:00"),
        ("February", "UTC", "1970-01-01T00:00:00+00:00", "1970-02-01T00:00:00+00:00"),
        ("today 16:40", "UTC", "1970-01-01T00:00:00+00:00", "1970-01-01T16:40:00+00:00"),
        ("today 16:40", "UTC", "1970-01-01T17:00:00+00:00", "1970-01-01T16:40:00+00:00"),
        ("07:00 16 July", "Europe/Stockholm", "1981-01-01T00:00:00+00:00", "1981-07-16T07:00:00+02:00"),
        ("today 16:40", "Europe/Stockholm", "1970-01-01T00:00:00+00:00", "1970-01-01T16:40:00+01:00"),
        ("Friday 10:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-21T10:00:00+01:00"),
        ("fredag 10:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-21T10:00:00+01:00"),
        ("7 minutes ago", "UTC", "2026-07-30T08:17:11+02:00", "2026-07-30T06:10:11+00:00"),
        ("in 7 minutes", "UTC", "2026-07-30T08:17:11+02:00", "2026-07-30T06:24:11+00:00"),
        ("two days ago", "UTC", "2026-07-30T08:17:11+02:00", "2026-07-28T06:17:11+00:00"),
        ("in three days", "UTC", "2026-07-30T08:17:11+02:00", "2026-08-02T06:17:11+00:00"),
    ])
    def test_relative_unbiased(self, human_string, tz, now, expected):
        future = parse(human_string=human_string, tz=tz, now=iso8601(now), bias="future")
        self.assertDatetimeEqual(future, expected)

        past = parse(human_string=human_string, tz=tz, now=iso8601(now), bias="past")
        self.assertDatetimeEqual(past, expected)

    @parameterized.expand([
        ("16/7", "UTC", "1970-01-01T00:00:00+00:00", "1970-07-16T00:00:00+00:00"),
        ("16/7", "UTC", "1970-08-01T00:00:00+00:00", "1971-07-16T00:00:00+00:00"),
        ("Friday 7:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-28T07:00:00+01:00"),
        ("fredag 7:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-28T07:00:00+01:00"),
        ("16:40", "UTC", "1970-01-01T00:00:00+00:00", "1970-01-01T16:40:00+00:00"),
        ("16:40", "UTC", "1970-01-01T17:00:00+00:00", "1970-01-02T16:40:00+00:00"),
        ("16:40", "Europe/Stockholm", "1970-01-01T00:00:00+00:00", "1970-01-01T16:40:00+01:00"),
        ("16:40", "Europe/Stockholm", "1981-07-01T00:00:00+00:00", "1981-07-01T16:40:00+02:00"),
        ("05:58", "Europe/Stockholm", "2025-03-31T06:19:40+00:00", "2025-04-01T05:58:00+02:00"),
        ("07:00", "UTC", "2025-03-31T06:00:00+00:00", "2025-03-31T07:00:00+00:00"),
        ("05:00", "UTC", "2025-03-31T06:00:00+00:00", "2025-04-01T05:00:00+00:00"),
        ("08:00", "Europe/Stockholm", "2026-03-28T09:00:00+01:00", "2026-03-29T08:00:00+02:00"),
    ])
    def test_relative_biased_future(self, human_string, tz, now, expected):
        future = parse(human_string=human_string, tz=tz, now=iso8601(now), bias="future")
        self.assertDatetimeEqual(future, expected)

        past = parse(human_string=human_string, tz=tz, now=iso8601(now), bias="past")
        self.assertDatetimeNotEqual(past, expected)

    @parameterized.expand([
        ("16/7", "UTC", "1970-01-01T00:00:00+00:00", "1969-07-16T00:00:00+00:00"),
        ("16/7", "UTC", "1970-08-01T00:00:00+00:00", "1970-07-16T00:00:00+00:00"),
        ("Friday 7:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-14T07:00:00+01:00"),
        ("fredag 7:00", "Europe/Stockholm", "2025-03-21T08:09:09+01:00", "2025-03-14T07:00:00+01:00"),
        ("9:50", "UTC", "1970-01-01T00:00:00+00:00", "1969-12-31T09:50:00+00:00"),
        ("16:40", "UTC", "1970-01-01T00:00:00+00:00", "1969-12-31T16:40:00+00:00"),
        ("16:40", "UTC", "1970-01-01T17:00:00+00:00", "1970-01-01T16:40:00+00:00"),
        ("16:40", "Europe/Stockholm", "1970-01-01T00:00:00+00:00", "1969-12-31T16:40:00+01:00"),
        ("16:40", "Europe/Stockholm", "1981-07-01T00:00:00+00:00", "1981-06-30T16:40:00+02:00"),
        ("05:58", "Europe/Stockholm", "2025-04-01T03:19:40+00:00", "2025-03-31T05:58:00+02:00"),
        ("07:00", "UTC", "2025-04-01T06:00:00+00:00", "2025-03-31T07:00:00+00:00"),
        ("05:00", "UTC", "2025-04-01T06:00:00+00:00", "2025-04-01T05:00:00+00:00"),
        ("08:00", "Europe/Stockholm", "2026-03-29T07:00:00+02:00", "2026-03-28T08:00:00+01:00"),
        ("7:15", "Europe/Stockholm", "2026-07-30T09:18:22+02:00", "2026-07-30T07:15:00+02:00"),
    ])
    def test_relative_biased_past(self, human_string, tz, now, expected):
        past = parse(human_string=human_string, tz=tz, now=iso8601(now), bias="past")
        self.assertDatetimeEqual(past, expected)

        future = parse(human_string=human_string, tz=tz, now=iso8601(now), bias="future")
        self.assertDatetimeNotEqual(future, expected)

    @pytest.mark.skip
    def test_local(self):
        tz = "Europe/Helsinki"
        now = datetime.now(tz=zoneinfo.ZoneInfo(tz))
        target = now + timedelta(hours=2)
        target = target.replace(minute=0, second=0, microsecond=0)
        s = f"{target.hour}:00"
        actual = parse(human_string=s, tz=tz)
        self.assertDatetimeEqual(actual, target)

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
        self.assertDatetimeEqual(actual, expected)

    def test_datetime_iso8601_roundtrip(self):
        for _ in range(100):
            xt = fresh.datetime()
            yt = parse(human_string=xt.isoformat(), now=fresh.datetime())
            self.assertDatetimeEqual(xt, yt)

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

class TimezoneBusinessDay(AssertDatetimeEqual, unittest.TestCase):
    @parameterized.expand([
        ("sista arbetsdagen innan 1 dec 16:28", "Europe/Stockholm", None, "2025-03-11T08:00:00+01:00", "2025-11-28T16:28:00+01:00"),
    ])
    def test_business_day(self, human_string, tz, country, now, expected):
        actual = parse(human_string=human_string, tz=tz, country=country, now=iso8601(now))
        self.assertDatetimeEqual(actual, expected)

class TimezoneTimezoneAndCountry(unittest.TestCase):
    @parameterized.expand([
        ("Europe/Stockholm", "SE"),
        ("America/New_York", "US"),
    ])
    def test_country_from_timezone(self, tz, country):
        assert figure_out_countrycode_from_timezone(tz) == country
