import builtins
import hashlib
import os
import random
import string
import zoneinfo

import datetime as the_datetime
from typing import Callable

def bool() -> bool:
    return random.choice([True, False])

coinflip = bool

def maybe[T](f: Callable[[], T]) -> T | None:
    if bool():
        return f()
    return None

def alphanum(N=12, prefix="") -> str:
    symbols = string.ascii_letters + string.digits
    return prefix + ''.join(random.choice(symbols) for i in range(N))

def set[T](f: Callable[[], T], min=0, max=5) -> set[T]:
    ts = builtins.set()
    for _ in range(0, random.randrange(min, max)):
        ts.add(f())
    return ts

def list[T](f: Callable[[], T], min=0, max=5) -> list[T]:
    ts = []
    for _ in range(0, random.randrange(min, max)):
        ts.append(f())
    return ts

def bytestring(N=12) -> bytes:
    return random.randbytes(N)

class Bytes:
    def __init__(self, bs=None, N=None):
        self.bs = bs
        if self.bs is None:
            self.bs = bytestring(N or 1024)

        self._sha256 = None
        self._blobid = None

    def __bytes__(self):
        return self.bs

    @property
    def sha256(self):
        if self._sha256 is None:
            self._sha256 = hashlib.sha256(self.bs).hexdigest()
        return self._sha256

    def __len__(self):
        return len(self.bs)

    @property
    def blobid(self):
        if self._blobid is None:
            h = hashlib.sha1()
            h.update(f"blob {len(self)}\u0000".encode())
            h.update(bytes(self))
            self._blobid = h.hexdigest()
        return self._blobid

    def dump(self, f):
        f.write(bytes(self))

Bytes.foo = Bytes("foo".encode("UTF-8"))

def tzinfo() -> the_datetime.tzinfo:
    match random.randrange(3):
        case 0:
            return the_datetime.UTC
        case 1:
            return zoneinfo.ZoneInfo("Europe/Stockholm")
        case 2: # local
            tz = the_datetime.datetime.now(the_datetime.UTC).astimezone().tzinfo
            assert tz is not None
            return tz
        case _:
            raise NotImplementedError()

def datetime(
    after: the_datetime.datetime | None = None,
    before: the_datetime.datetime | None = None,
    tz: the_datetime.tzinfo | None = None,
    after_inclusive=True,
) -> the_datetime.datetime:
    if after is not None:
        tz = tz or after.tzinfo
    if before is not None:
        tz = tz or before.tzinfo
    tz = tz or tzinfo()

    if after is None:
        after = the_datetime.datetime(1970, 1, 1, tzinfo=tz)
    else:
        after = after.astimezone(tz)

    choice = random.randrange(10)
    if choice == 0 or choice == 1:
        if choice == 0 and after_inclusive:
            return after
        return after + the_datetime.datetime.resolution

    if before is None:
        before = the_datetime.datetime.now(tz) + the_datetime.timedelta(days=100*365)
    elif choice == 2:
        return before.astimezone(tz) - the_datetime.datetime.resolution

    a = after.timestamp()
    b = before.astimezone(tz).timestamp()
    ts = a + (b - a)*random.random()
    return the_datetime.datetime.fromtimestamp(ts, tz=tz)

def timedelta(positive=None) -> the_datetime.timedelta:
    if positive:
        ms = random.randrange(1, 1_000_000)
    else:
        if coinflip():
            ms = 0
        else:
            ms = random.randrange(1, 1_000_000)

    match random.randrange(5):
        case 0:
            if positive:
                return the_datetime.timedelta(seconds=0, microseconds=ms)
            else:
                return the_datetime.timedelta(seconds=0)
        case 1:
            return the_datetime.timedelta(seconds=0, microseconds=ms)
        case 2:
            return the_datetime.timedelta(seconds=random.randrange(3600), microseconds=ms)
        case 3:
            return the_datetime.timedelta(seconds=random.randrange(3600*24), microseconds=ms)
        case 4:
            return the_datetime.timedelta(seconds=random.randrange(3600*24*365*10), microseconds=ms)
        case _:
            raise NotImplementedError()

class Seed:
    seed = os.environ.get("TESTS_RANDOM_SEED") or str(random.getrandbits(64))
    def setUp(self):
        random.seed(self.seed)
        super().setUp()
