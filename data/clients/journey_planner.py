"""HTTP client for the Entur Journey Planner v3 GraphQL API."""

from __future__ import annotations

import httpx

from data.queries.trip_query import TRIP_QUERY, trip_variables
from data.queries.quay_query import QUAY_DEPARTURES_QUERY, quay_variables

JOURNEY_PLANNER_URL = "https://api.entur.io/journey-planner/v3/graphql"
HEADERS = {
    "ET-Client-Name": "entur-pendlerkompis",
    "Content-Type": "application/json",
}


async def _post(client: httpx.AsyncClient, query: str, variables: dict) -> dict:
    resp = await client.post(
        JOURNEY_PLANNER_URL,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=30.0,
    )
    resp.raise_for_status()
    body = resp.json()
    if "errors" in body:
        raise RuntimeError(f"GraphQL errors: {body['errors']}")
    return body["data"]


async def query_trips(
    from_coords: tuple[float, float],
    to_coords: tuple[float, float],
    date_time: str,
    num_patterns: int = 5,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Query Journey Planner for trip alternatives."""
    variables = trip_variables(from_coords, to_coords, date_time, num_patterns)
    if client is None:
        async with httpx.AsyncClient() as c:
            return await _post(c, TRIP_QUERY, variables)
    return await _post(client, TRIP_QUERY, variables)


async def query_quay_departures(
    quay_id: str,
    num_departures: int = 20,
    time_range: int = 7200,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Query estimated calls at a specific quay."""
    variables = quay_variables(quay_id, num_departures, time_range)
    if client is None:
        async with httpx.AsyncClient() as c:
            return await _post(c, QUAY_DEPARTURES_QUERY, variables)
    return await _post(client, QUAY_DEPARTURES_QUERY, variables)
