"""Client for the Entur realtime invalid-ET GraphQL API.

Falls back to computing delay data from Journey Planner historical trips
if the invalid-ET endpoint is not accessible.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from data.clients.journey_planner import query_trips

INVALID_ET_URL = "https://api.entur.io/realtime/invalid-et/graphql"
HEADERS = {
    "ET-Client-Name": "entur-pendlerkompis",
    "Content-Type": "application/json",
}

# GraphQL query for the invalid-ET API (fetch arrival times by datedServiceJourneyId)
ARRIVAL_QUERY = """
query RecentArrivals($serviceJourneyIds: [String!]!) {
  estimatedCalls(serviceJourneyIds: $serviceJourneyIds) {
    aimedArrivalTime
    expectedArrivalTime
    actualArrivalTime
    cancellation
    quay { id name }
    serviceJourney {
      id
      line { publicCode transportMode }
    }
  }
}
"""


async def query_invalid_et(
    service_journey_ids: list[str],
    client: httpx.AsyncClient | None = None,
) -> dict | None:
    """Try to query the invalid-ET API. Returns None if the endpoint is unavailable."""
    try:
        variables = {"serviceJourneyIds": service_journey_ids}
        c = client or httpx.AsyncClient()
        try:
            resp = await c.post(
                INVALID_ET_URL,
                json={"query": ARRIVAL_QUERY, "variables": variables},
                headers=HEADERS,
                timeout=10.0,
            )
            if resp.status_code >= 400:
                return None
            body = resp.json()
            if "errors" in body:
                return None
            return body.get("data")
        finally:
            if client is None:
                await c.aclose()
    except (httpx.HTTPError, Exception):
        return None


async def query_recent_arrivals(
    from_coords: tuple[float, float],
    to_coords: tuple[float, float],
    date_time: str,
    lookback_hours: int = 2,
    num_patterns: int = 10,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Fetch recent trip data for the same route, looking back in time.

    Queries the Journey Planner for trips departing `lookback_hours` before
    the given `date_time`. These represent recent/past departures whose
    expected vs aimed times give us empirical delay information.
    """
    dt = datetime.fromisoformat(date_time)
    historical_dt = (dt - timedelta(hours=lookback_hours)).isoformat()
    return await query_trips(
        from_coords, to_coords, historical_dt, num_patterns, client
    )
