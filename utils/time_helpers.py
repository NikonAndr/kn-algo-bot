from datetime import datetime
from zoneinfo import ZoneInfo

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

def warsaw_now():
    return datetime.now(WARSAW_TZ).replace(tzinfo=None)

def to_warsaw_naive(aware_dt):
    return aware_dt.astimezone(WARSAW_TZ).replace(tzinfo=None)

def parse_naive_timestamp(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
