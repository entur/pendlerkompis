"""HTTP client for MET Norway Locationforecast 2.0 (Yr) weather data."""

from __future__ import annotations

from datetime import datetime

import httpx

LOCATIONFORECAST_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

# MET.no requires a meaningful User-Agent identifying the application and contact.
USER_AGENT = "pendlerkompis/1.0 github.com/entur/pendlerkompis"


async def query_weather_forecast(
    lat: float,
    lon: float,
    target_time: datetime,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Fetch weather forecast from MET.no and return the entry closest to target_time.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.
        target_time: The datetime to find the closest forecast for.

    Returns:
        Raw timeseries entry dict from Locationforecast closest to target_time,
        or empty dict if the request fails.
    """
    headers = {"User-Agent": USER_AGENT}
    params = {"lat": round(lat, 4), "lon": round(lon, 4)}

    async def _fetch(c: httpx.AsyncClient) -> dict:
        resp = await c.get(
            LOCATIONFORECAST_URL,
            params=params,
            headers=headers,
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()

        timeseries = data.get("properties", {}).get("timeseries", [])
        if not timeseries:
            return {}

        # Find entry closest to target_time
        target_ts = target_time.timestamp()
        best_entry = None
        best_diff = float("inf")
        for entry in timeseries:
            entry_time = datetime.fromisoformat(entry["time"])
            diff = abs(entry_time.timestamp() - target_ts)
            if diff < best_diff:
                best_diff = diff
                best_entry = entry

        return best_entry or {}

    if client is None:
        async with httpx.AsyncClient() as c:
            return await _fetch(c)
    return await _fetch(client)
