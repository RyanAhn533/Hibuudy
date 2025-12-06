# utils/runtime.py
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple


def parse_hhmm_to_time(hhmm: str) -> time:
    if not isinstance(hhmm, str):
        return time(0, 0)
    try:
        hh, mm = hhmm.split(":")
        return time(int(hh), int(mm))
    except Exception:
        return time(0, 0)


def find_active_item(
    schedule: List[Dict],
    now: Optional[time] = None,
) -> Tuple[Optional[Dict], Optional[Dict]]:
    if not schedule:
        return None, None

    if now is None:
        now = datetime.now().time()

    sorted_items = sorted(schedule, key=lambda it: parse_hhmm_to_time(it.get("time", "00:00")))

    active = None
    next_item = None

    for item in sorted_items:
        t = parse_hhmm_to_time(item.get("time", "00:00"))
        if t <= now:
            active = item
        elif t > now and next_item is None:
            next_item = item

    if active is None:
        next_item = sorted_items[0]

    return active, next_item


def annotate_schedule_with_status(
    schedule: List[Dict],
    now: Optional[time] = None,
) -> List[Dict]:
    if now is None:
        now = datetime.now().time()

    active, _ = find_active_item(schedule, now)
    active_id = id(active) if active is not None else None

    annotated = []
    for item in schedule:
        t = parse_hhmm_to_time(item.get("time", "00:00"))

        if active_id is not None and id(item) == active_id:
            status = "active"
        elif t < now:
            status = "past"
        else:
            status = "upcoming"

        new_item = dict(item)
        new_item["status"] = status
        annotated.append(new_item)

    return annotated
