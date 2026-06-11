from time import mktime, localtime, time as now

FULL_RES_DAYS = 7
MAX_ROWS      = 4320
TRIM_TO       = 4000
CSV_PATH      = "history.csv"
HEADER        = "timestamp,temp_dht,humidity,temp_board,light_level\n"


def _parse_ts(ts_str):
    # "2026-06-08T14:30:00"
    try:
        date, t = ts_str.split("T")
        y, mo, d = date.split("-")
        h, mi, s = t.split(":")
        return mktime((int(y), int(mo), int(d),
                       int(h), int(mi), int(s), 0, 0))
    except:
        return None


def _compress(lines):
    """
    For rows older than FULL_RES_DAYS, keep only one per hour (the first
    reading seen for that UTC hour). Recent rows are kept as-is.
    """
    cutoff = now() - FULL_RES_DAYS * 86400
    compressed = [lines[0]]  # always keep header
    seen_hours = set()

    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) < 5:
            continue

        ts_epoch = _parse_ts(parts[0])
        if ts_epoch is None:
            continue

        if ts_epoch >= cutoff:
            # Within full-res window, keep everything
            compressed.append(line)
        else:
            # Beyond window — keep only first reading per hour
            t       = localtime(ts_epoch)
            hour_key = (t[0], t[1], t[2], t[3])  # (year, month, day, hour)
            if hour_key not in seen_hours:
                seen_hours.add(hour_key)
                compressed.append(line)

    return compressed


# make sure history log is created
def _ensure_file():
    try:
        open(CSV_PATH, "r").close()
    except:
        with open(CSV_PATH, "w") as f:
            f.write(HEADER)


def append_reading(ts, temp_dht, humidity, temp_board, light_level):
    _ensure_file()

    with open(CSV_PATH, "r") as f:
        lines = f.readlines()

    if not lines or not lines[0].startswith("timestamp"):
        lines = [HEADER] + lines

    lines.append(f"{ts},{temp_dht},{humidity},{temp_board},{light_level}\n")

    # Compress old data first, then hard-cap if still over
    lines = _compress(lines)
    if len(lines) > MAX_ROWS + 1:
        lines = [lines[0]] + lines[-(TRIM_TO):]

    with open(CSV_PATH, "w") as f:
        for line in lines:
            f.write(line)


def read_csv():
    _ensure_file()
    try:
        with open(CSV_PATH, "r") as f:
            return f.read()
    except Exception as e:
        print("storage read_csv error:", e)
        return HEADER