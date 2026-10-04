"""Independent exhaustive offset oracle for the recorded representation rule."""
import datetime as dt


def represented_seconds(value):
    parsed = dt.datetime.fromisoformat(value)
    return parsed.toordinal()*86400 + parsed.hour*3600 + parsed.minute*60 + parsed.second - int(parsed.utcoffset().total_seconds())


def expected_wire(local):
    offset = int(local.utcoffset().total_seconds())
    instant = represented_seconds(local.isoformat())
    low = dt.date.min.toordinal()*86400
    high = dt.date.max.toordinal()*86400 + 86399
    # Exhaustively search the RFC3339 numeric-offset domain. This independent
    # reference does not use a production rounding or serialization helper.
    candidates = [(abs(minutes*60-offset), minutes) for minutes in range(-1439, 1440)
                  if low <= instant+minutes*60 <= high]
    if not candidates:
        raise ValueError("No representable RFC3339 calendar and numeric offset")
    _, minutes = min(candidates)
    wall = instant+minutes*60
    ordinal, remainder = divmod(wall, 86400)
    date = dt.date.fromordinal(ordinal)
    hour, remainder = divmod(remainder, 3600)
    minute, second = divmod(remainder, 60)
    sign = "+" if minutes >= 0 else "-"
    magnitude = abs(minutes)
    return f"{date.isoformat()}T{hour:02}:{minute:02}:{second:02}{sign}{magnitude//60:02}:{magnitude%60:02}"
