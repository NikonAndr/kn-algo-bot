from datetime import datetime
from zoneinfo import ZoneInfo

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

def warsaw_now():
    return datetime.now(WARSAW_TZ).replace(tzinfo=None)
