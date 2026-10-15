import datetime
import logging
from typing import cast

import pytz

from . import package_name


# https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
def is_aware(x: datetime.datetime | datetime.time) -> bool:
    match type(x):
        case datetime.datetime:
            if x.tzinfo is None:
                return False
            if x.tzinfo.utcoffset(cast(datetime.datetime, x)) is None:
                return False
        case datetime.time:
            if x.tzinfo is None:
                return False
            if x.tzinfo.utcoffset(None):
                return False
    return True

# https://stackoverflow.com/a/13020785
def figure_out_countrycode_from_timezone(tz: str | datetime.tzinfo) -> str | None:
    tz = str(tz)
    for k, v in pytz.country_timezones.items():
        if tz in v:
            return k
    return None

def setup_logger(level, logger=None, name=None):
    level = level.upper()
    if logger is None:
        logger = logging.getLogger(name=name or package_name)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    logger.addHandler(handler)

    fmt = logging.Formatter(fmt="%(asctime)s:%(name)s:%(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z")
    handler.setFormatter(fmt)

def truncate(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)
