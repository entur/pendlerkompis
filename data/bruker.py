"""User profile management. Hardcoded Rolf for the hackathon."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from data.models import Bruker

CET = timezone(timedelta(hours=1))

ROLF: Bruker = {
    "id": "rolf-1",
    "hjem": {
        "navn": "Drammen",
        "koordinater": {"lat": 59.7441, "lon": 10.2045},
    },
    "jobb": {
        "navn": "Raadhusgata 5, Oslo",
        "koordinater": {"lat": 59.9118, "lon": 10.7340},
    },
    "avreisetider": {
        "fra_hjem": "07:15",
        "fra_jobb": "16:30",
    },
    "preferanser": {
        "laert": [
            {
                "situasjon": "signalfeil",
                "valgt_handling": "reis_tidligere",
                "antall_ganger": 3,
            }
        ]
    },
}


def get_bruker() -> Bruker:
    return ROLF


def get_trip_params(direction: str = "fra_jobb", override_time: str | None = None) -> dict:
    """Return origin/destination coords and departure datetime for a direction.

    Args:
        direction: "fra_hjem" or "fra_jobb"
        override_time: Optional "HH:MM" string to override the profile departure time.

    Returns:
        dict with keys: from_coords, to_coords, date_time (ISO-8601 string)
    """
    bruker = get_bruker()
    if direction == "fra_hjem":
        from_sted = bruker["hjem"]
        to_sted = bruker["jobb"]
        time_str = override_time or bruker["avreisetider"]["fra_hjem"]
    else:
        from_sted = bruker["jobb"]
        to_sted = bruker["hjem"]
        time_str = override_time or bruker["avreisetider"]["fra_jobb"]

    hour, minute = map(int, time_str.split(":"))
    now = datetime.now(CET)
    departure = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if departure < now:
        departure += timedelta(days=1)

    return {
        "from_coords": (
            from_sted["koordinater"]["lat"],
            from_sted["koordinater"]["lon"],
        ),
        "to_coords": (
            to_sted["koordinater"]["lat"],
            to_sted["koordinater"]["lon"],
        ),
        "date_time": departure.isoformat(),
    }
