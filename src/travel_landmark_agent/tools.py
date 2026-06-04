"""Bespoke tools."""

from datetime import datetime, timedelta

from beeai_framework.tools import tool


@tool
def get_local_dates() -> str:
    """Return the local dates for today, and for the next Saturday and Sunday."""
    today = datetime.now()
    next_saturday = _get_next_saturday(today)
    next_sunday = next_saturday + timedelta(days=1)
    return "\n".join(
        [
            f"Current local date: {today.date().isoformat()}",
            f"Next weekend start date: {next_saturday.date().isoformat()}",
            f"Next weekend end date: {next_sunday.date().isoformat()}",
        ]
    )


def _get_next_saturday(today: datetime) -> datetime:
    days_ahead = (5 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7

    return today + timedelta(days=days_ahead)
