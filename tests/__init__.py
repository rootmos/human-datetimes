import datetime
import importlib.resources

def asset(fn, mode="r"):
    assert mode[0] == "r"
    return open(importlib.resources.files(__name__).joinpath("assets", fn), mode)

def iso8601(x):
    if x is None:
        return None
    elif isinstance(x, str):
        return datetime.datetime.fromisoformat(x)
    elif isinstance(x, datetime.datetime):
        return x.isoformat(timespec="seconds")
