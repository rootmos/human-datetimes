import datetime
import shutil
import subprocess
import zoneinfo

from typing import cast
from dataclasses import dataclass

import cron_converter
import dateparser
import dateutil.parser

from . import business_day, utils

import logging
logger = logging.getLogger(__name__)

@dataclass
class Context:
    now: datetime.datetime
    _now: datetime.datetime | None
    tz: str
    _tz: str | None
    tzinfo: datetime.tzinfo
    country: str | None

    def __init__(self, now=None, tz=None, country=None):
        self._now = now

        if self._now is not None:
            self.now = self._now
        else:
            self.now = self._now or datetime.datetime.now(datetime.UTC)
        assert utils.is_aware(self.now)

        self._tz = tz
        if self._tz is not None:
            self.tz = self._tz
            self.tzinfo = zoneinfo.ZoneInfo(self._tz)
        else:
            self.tzinfo = cast(datetime.tzinfo, self.now.tzinfo) # from assert.is_aware(self.now)
            self.tz = str(self.now.tzinfo)

        self.country = country
        if self.country is None:
            self.country = utils.figure_out_countrycode_from_timezone(self.tz)

    def parse(self, human_string):
        try:
            dt = cron_converter.Cron(human_string).schedule(self.now.astimezone(self.tzinfo)).next()
            logger.debug("cron format succeeded; %s: %s", human_string, dt)
            assert utils.is_aware(dt)
            return dt
        except ValueError:
            logger.debug("cron format failed: %s", human_string)
            pass

        try:
            logger.debug("trying datetime.datetime.fromisoformat: %s", human_string)
            dt = datetime.datetime.fromisoformat(human_string)
            if not utils.is_aware(dt):
                return dt.replace(tzinfo=self.tzinfo)
            return dt
        except ValueError:
            pass

        exe = shutil.which("date")
        if exe and self._now is None:
            try:
                logger.debug("attempting `date`: %s", human_string)
                output = subprocess.check_output([exe, "-Is", "--date=" + human_string], text=True, env={"TZ": self.tz or str(self.tzinfo)}, stderr=subprocess.DEVNULL)
                return datetime.datetime.fromisoformat(output.splitlines()[0])
            except subprocess.CalledProcessError:
                pass

        try:
            logger.debug("trying datetime.time.fromisoformat: %s", human_string)
            t = datetime.time.fromisoformat(human_string)
            if utils.is_aware(t):
                raise NotImplementedError()

            dt = datetime.datetime.combine(self.now.date(), t, tzinfo=self.tzinfo)
            if dt < self.now:
                dt += datetime.timedelta(days=1)
            return dt
        except ValueError:
            pass

        try:
            logger.debug("trying dateutil.parser.parse: %s", human_string)

            class CustomParserInfo(dateutil.parser.parserinfo):
                MONTHS = [
                    ("Jan", "January", "jan", "januari"),
                    ("Feb", "February", "feb", "februari"),
                    ("Mar", "March", "mar", "mars"),
                    ("Apr", "April", "apr", "april"),
                    ("May", "May", "maj"),
                    ("Jun", "June", "jun", "juni"),
                    ("Jul", "July", "jul", "juli"),
                    ("Aug", "August", "aug", "augusti"),
                    ("Sep", "Sept", "September", "sep", "september"),
                    ("Oct", "October", "okt", "oktober"),
                    ("Nov", "November", "nov", "november"),
                    ("Dec", "December", "dec", "december"),
                ]

                WEEKDAYS = [
                    ("Mon", "Monday", "mån", "måndag"),
                    ("Tue", "Tuesday", "tis", "tisdag"),
                    ("Wed", "Wednesday", "ons", "onsdag"),
                    ("Thu", "Thursday", "tor", "torsdag"),
                    ("Fri", "Friday", "fre", "fredag"),
                    ("Sat", "Saturday", "lör", "lördag"),
                    ("Sun", "Sunday", "sön", "söndag"),
                ]

            dt = dateutil.parser.parse(
                timestr = human_string,
                parserinfo = CustomParserInfo(),
                default = self.now.replace(hour=0, minute=0, second=0, microsecond=0),
            ).replace(tzinfo=self.tzinfo)
            assert utils.is_aware(dt)
            if dt >= self.now:
                return dt
        except dateutil.parser.ParserError:
            pass

        settings = {
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
        }
        if self.tz is not None:
            settings["TIMEZONE"] = self.tz
            settings["TO_TIMEZONE"] = self.tz
            settings["RELATIVE_BASE"] = self.now.astimezone(self.tzinfo)
        else:
            settings["RELATIVE_BASE"] = self.now

        logger.debug("attempting dateparser: %s", human_string)
        logger.debug("dateparser settings: %s", settings)
        dt = dateparser.parse(human_string, settings = settings)
        if dt is None:
            raise ValueError("unable to parse as datetime", human_string, self)
        assert utils.is_aware(dt)
        return dt

def parse_schedule(human_string, tz=None, now=None, country=None):
    ctx = Context(now=now, tz=tz, country=country)
    logger.debug("parsing: %s %s", human_string, ctx)

    if ctx.country is not None:
        try:
            bdp = business_day.parse(human_string, country=ctx.country, datetime_parser=ctx.parse)
            if bdp is not None:
                assert utils.is_aware(bdp)
                return bdp
        except ValueError:
            pass

    return ctx.parse(human_string)
