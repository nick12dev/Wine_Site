from decimal import (
    Decimal,
    InvalidOperation,
)


def to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def to_decimal(v):
    try:
        return Decimal(v)
    except (ValueError, TypeError, InvalidOperation):
        return None


def normalize_text(text):
    return ' '.join((text or '').split())
