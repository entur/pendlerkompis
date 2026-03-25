"""HTTP clients for car travel data: OSRM routing + Vegvesen Trafikkdata."""

from __future__ import annotations

from datetime import datetime, timedelta

import httpx

OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
TRAFIKKDATA_URL = "https://trafikkdata-api.atlas.vegvesen.no/"

# Representative E18 stations along the Drammen–Oslo corridor.
# Ordered geographically from Drammen to Oslo.
E18_STATIONS: list[dict[str, str]] = [
    {"id": "09988V1206753", "name": "E18 Bangeløkka Sydgående"},
    {"id": "38517V180819", "name": "E18 Tranby X"},
    {"id": "86203V625294", "name": "E18 Drammensv v/Maritim"},
    {"id": "52231V625294", "name": "Frognerstranda (E18)"},
    {"id": "44417V1717891", "name": "E18 Bangeløkka Nordgående"},
]


async def query_osrm_route(
    from_coords: tuple[float, float],
    to_coords: tuple[float, float],
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Get free-flow driving route from OSRM.

    Args:
        from_coords: (lat, lon) origin
        to_coords: (lat, lon) destination

    Returns:
        {"avstand_km": float, "reisetid_fri_flyt_min": float}
    """
    # OSRM expects lon,lat order
    url = f"{OSRM_URL}/{from_coords[1]},{from_coords[0]};{to_coords[1]},{to_coords[0]}?overview=false"

    async def _fetch(c: httpx.AsyncClient) -> dict:
        resp = await c.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            raise RuntimeError(f"OSRM error: {data.get('code', 'unknown')}")
        route = data["routes"][0]
        return {
            "avstand_km": round(route["distance"] / 1000, 1),
            "reisetid_fri_flyt_min": round(route["duration"] / 60, 1),
        }

    if client is None:
        async with httpx.AsyncClient() as c:
            return await _fetch(c)
    return await _fetch(client)


def _volume_query(station_id: str, from_dt: str, to_dt: str) -> dict:
    """Build a GraphQL request body for a single station's hourly volume."""
    query = """
    query($id: String!, $from: ZonedDateTime!, $to: ZonedDateTime!) {
      trafficData(trafficRegistrationPointId: $id) {
        trafficRegistrationPoint { id name }
        volume {
          byHour(from: $from, to: $to) {
            edges {
              node {
                from
                to
                total {
                  volumeNumbers { volume }
                  coverage { percentage }
                }
              }
            }
          }
        }
      }
    }
    """
    return {
        "query": query,
        "variables": {"id": station_id, "from": from_dt, "to": to_dt},
    }


async def _post_trafikkdata(client: httpx.AsyncClient, body: dict) -> dict:
    resp = await client.post(TRAFIKKDATA_URL, json=body, timeout=15.0)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"Trafikkdata errors: {data['errors']}")
    return data.get("data", {})


async def query_current_volume(
    now: datetime,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    """Fetch the most recent available hourly volume for E18 corridor stations.

    The Trafikkdata API has a ~3 hour publication lag, so we query a 6-hour
    window ending at the current hour and take the latest available bucket.

    Returns list of {"station_id", "station_name", "volume", "time_bucket"} dicts.
    """
    hour_end = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    hour_start = hour_end - timedelta(hours=6)
    from_dt = hour_start.isoformat()
    to_dt = hour_end.isoformat()

    async def _fetch(c: httpx.AsyncClient) -> list[dict]:
        results = []
        for station in E18_STATIONS:
            try:
                body = _volume_query(station["id"], from_dt, to_dt)
                data = await _post_trafikkdata(c, body)
                td = data.get("trafficData", {})
                edges = td.get("volume", {}).get("byHour", {}).get("edges", [])
                if edges:
                    # Take the most recent (last) available bucket
                    latest = edges[-1]["node"]
                    volume = latest["total"]["volumeNumbers"]["volume"]
                    time_bucket = latest["from"]
                else:
                    volume = 0
                    time_bucket = None
                results.append({
                    "station_id": station["id"],
                    "station_name": station["name"],
                    "volume": volume,
                    "time_bucket": time_bucket,
                })
            except Exception:
                results.append({
                    "station_id": station["id"],
                    "station_name": station["name"],
                    "volume": 0,
                    "time_bucket": None,
                })
        return results

    if client is None:
        async with httpx.AsyncClient() as c:
            return await _fetch(c)
    return await _fetch(client)


async def query_historical_volume(
    now: datetime,
    num_weeks: int = 4,
    hour_override: int | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, float]:
    """Fetch average volume for same hour + weekday over the last N weeks.

    Args:
        hour_override: If set, use this hour instead of now.hour.
            Useful when current-volume data is lagged (e.g., latest
            available is 09:00 but it's 13:00 now).

    Returns {"station_id": avg_volume} dict.
    """
    hour = hour_override if hour_override is not None else now.hour
    weekday = now.weekday()

    # Build list of same-weekday dates going back num_weeks
    dates: list[datetime] = []
    d = now - timedelta(days=7)
    while len(dates) < num_weeks:
        if d.weekday() == weekday:
            dates.append(d)
            d -= timedelta(days=7)
        else:
            d -= timedelta(days=1)

    async def _fetch(c: httpx.AsyncClient) -> dict[str, float]:
        station_totals: dict[str, list[int]] = {s["id"]: [] for s in E18_STATIONS}
        for date in dates:
            hour_start = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            from_dt = hour_start.isoformat()
            to_dt = (hour_start + timedelta(hours=1)).isoformat()
            for station in E18_STATIONS:
                try:
                    body = _volume_query(station["id"], from_dt, to_dt)
                    data = await _post_trafikkdata(c, body)
                    td = data.get("trafficData", {})
                    edges = td.get("volume", {}).get("byHour", {}).get("edges", [])
                    vol = edges[0]["node"]["total"]["volumeNumbers"]["volume"] if edges else 0
                    if vol > 0:
                        station_totals[station["id"]].append(vol)
                except Exception:
                    pass
        return {
            sid: round(sum(vols) / len(vols)) if vols else 0
            for sid, vols in station_totals.items()
        }

    if client is None:
        async with httpx.AsyncClient() as c:
            return await _fetch(c)
    return await _fetch(client)
