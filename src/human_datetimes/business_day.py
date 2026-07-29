import datetime
import re

import holidays

def find_business_day(year, month, day, country: str, towards=0, offset=0) -> datetime.date | None:
    country_holidays = holidays.country_holidays(country) # TODO cache these?
    d = datetime.date(year=year, month=month, day=day)
    d += datetime.timedelta(days=offset)

    is_weekend = lambda d: d.isoweekday() >= 6
    is_holiday = lambda d: d in country_holidays
    if towards == 0:
        if not is_weekend(d) and not is_holiday(d):
            return None
    else:
        towards = 1 if towards > 0 else -1

    while is_weekend(d) or is_holiday(d):
        d = d.replace(day = d.day + towards)
    return d

class Phrases:
    before = {
        "en": r"last\s+business\s+day\s+before",
        "se": r"sista\s+arbetsdagen\s+innan",
    }

    on_or_after = {
        "en": r"next\s+business\s+day",
        "se": r"nästa\s+arbetsdag",
    }

def parse(s, country, datetime_parser):
    def go(phrases):
        for _, p in phrases.items():
            m = re.fullmatch(r"\s*" + p + r"\s+(.*)", s)
            if m is None:
                continue
            return m[1]

    for (towards, offset, phrases) in [
        (-1, -1, Phrases.before),
        ( 1,  0, Phrases.on_or_after),
    ]:
        m = go(phrases)
        if m is None:
            continue

        dt = datetime_parser(m)

        d = find_business_day(year=dt.year, month=dt.month, day=dt.day, country=country, towards=towards, offset=offset)
        return datetime.datetime.combine(d, dt.time(), tzinfo=dt.tzinfo)
