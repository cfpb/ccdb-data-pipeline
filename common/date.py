import time
from datetime import datetime


def parse_date(date_str):
    if not date_str:
        return None

    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass

    return None


def format_date_est(date_str):
    """format the date at noon Eastern Standard Time"""
    d = parse_date(date_str)
    if not d:
        return None
    return d.strftime("%Y-%m-%d") + 'T12:00:00-05:00'


def format_date_as_mdy(date_str):
    d = parse_date(date_str)
    if not d:
        return None
    return d.strftime("%m/%d/%y")


def now_as_string():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
