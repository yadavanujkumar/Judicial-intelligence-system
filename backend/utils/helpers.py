import re
from datetime import datetime
from typing import Optional


def format_date(date_obj) -> Optional[str]:
    """Return ISO-8601 string for a date/datetime object, or None."""
    if date_obj is None:
        return None
    if isinstance(date_obj, str):
        return date_obj
    try:
        return date_obj.strftime("%Y-%m-%d")
    except Exception:
        return None


def calculate_days_between(start, end) -> Optional[int]:
    """Return the number of days between two dates/strings."""
    try:
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        return max(0, (end - start).days)
    except Exception:
        return None


def clean_text(text: str) -> str:
    """Remove excessive whitespace and non-printable characters."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x20-\x7E\u0900-\u097F]", "", text)
    return text.strip()


_label_maps: dict[str, dict] = {}
_reverse_maps: dict[str, dict] = {}


def encode_label(value: str, namespace: str = "default") -> int:
    """Encode a string label to an integer, building the map lazily."""
    if namespace not in _label_maps:
        _label_maps[namespace] = {}
        _reverse_maps[namespace] = {}
    mapping = _label_maps[namespace]
    if value not in mapping:
        mapping[value] = len(mapping)
        _reverse_maps[namespace][mapping[value]] = value
    return mapping[value]


def decode_label(code: int, namespace: str = "default") -> Optional[str]:
    """Decode an integer code back to its string label."""
    return _reverse_maps.get(namespace, {}).get(code)
