"""Pendlerkompis data layer — orchestrator and CLI entry point.

Fetches travel data from Entur APIs and outputs extended Kontrakt A JSON
for the motor (Spor 2).

Usage:
    python -m data.main --direction fra_jobb [--time 16:30]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime

import httpx

from data.bruker import get_bruker, get_trip_params
from data.clients.journey_planner import query_trips, query_quay_departures
from data.clients.realtime import query_recent_arrivals, query_invalid_et
from data.clients.road import query_osrm_route, query_current_volume, query_historical_volume
from data.clients.weather import query_weather_forecast
from data.models import KontraktAUtvidet
from data.transform import (
    build_bildata,
    build_kontrakt_a,
    build_vaerdata,
    compute_delay_statistics,
    extract_destination_quay_ids,
    extract_faktiske_ankomster,
    extract_innstillinger,
    extract_line_codes,
    extract_service_journey_ids,
    transform_trip_response,
)


async def hent_pendlerdata(
    direction: str = "fra_jobb",
    override_time: str | None = None,
) -> KontraktAUtvidet:
    """Main entry point. Fetches all data and returns extended Kontrakt A.

    Steps:
    1. Load user profile
    2. Query Journey Planner for current trip alternatives
    3. Extract situations (avviksmeldinger)
    4. Identify destination quay + lines from results
    5. Query historical trips (2h before) for recent delay data
    6. Query quay departures for live cancellation data
    7. Query OSRM + Vegvesen Trafikkdata for car travel alternative
    8. Try invalid-ET API for actual arrivals, fall back to historical trips
    9. Compute delay statistics
    10. Assemble extended Kontrakt A
    """
    bruker = get_bruker()
    params = get_trip_params(direction, override_time)

    async with httpx.AsyncClient() as client:
        # Step 1: Current trip alternatives
        print("Fetching current trip alternatives...", file=sys.stderr)
        current_data = await query_trips(
            params["from_coords"],
            params["to_coords"],
            params["date_time"],
            num_patterns=5,
            client=client,
        )

        avvik, alternativer = transform_trip_response(current_data)
        dest_quay_ids = extract_destination_quay_ids(current_data)
        line_codes = extract_line_codes(current_data)

        # Determine destination name for statistics
        dest_name = bruker["hjem"]["navn"] if direction == "fra_jobb" else bruker["jobb"]["navn"]

        # Steps 2+3+4: Historical trips + quay departures + car data (parallel)
        print(f"Fetching historical trips, quay departures for {len(dest_quay_ids)} quay(s), and car data...", file=sys.stderr)
        now = datetime.now().astimezone()

        historical_task = query_recent_arrivals(
            params["from_coords"],
            params["to_coords"],
            params["date_time"],
            lookback_hours=2,
            num_patterns=10,
            client=client,
        )

        quay_tasks = [
            query_quay_departures(qid, num_departures=20, client=client)
            for qid in dest_quay_ids
        ]

        osrm_task = query_osrm_route(params["from_coords"], params["to_coords"], client=client)
        volume_task = query_current_volume(now, client=client)

        # Weather forecast at departure location
        departure_coords = params["from_coords"]
        departure_dt = datetime.fromisoformat(params["date_time"])
        weather_task = query_weather_forecast(
            departure_coords[0], departure_coords[1], departure_dt, client=client
        )

        results = await asyncio.gather(
            historical_task, osrm_task, volume_task, weather_task,
            *quay_tasks,
            return_exceptions=True,
        )
        historical_data = results[0] if not isinstance(results[0], Exception) else {"trip": {"tripPatterns": []}}
        osrm_result = results[1] if not isinstance(results[1], Exception) else None
        current_volumes = results[2] if not isinstance(results[2], Exception) else []
        weather_entry = results[3] if not isinstance(results[3], Exception) else {}
        quay_results = [r for r in results[4:] if not isinstance(r, Exception)]

        # Determine the hour of the latest available volume data and fetch
        # historical averages for that same hour (Trafikkdata has ~3h lag)
        data_hour = None
        for cv in current_volumes:
            tb = cv.get("time_bucket")
            if tb:
                try:
                    data_hour = datetime.fromisoformat(tb).hour
                except (ValueError, TypeError):
                    pass
                break
        historical_avgs = await query_historical_volume(
            now, num_weeks=4, hour_override=data_hour, client=client,
        )

        # Step 4: Try invalid-ET for actual arrival data
        historical_sj_ids = extract_service_journey_ids(historical_data)
        et_data = None
        if historical_sj_ids:
            print(f"Trying invalid-ET API for {len(historical_sj_ids)} service journeys...", file=sys.stderr)
            et_data = await query_invalid_et(historical_sj_ids, client=client)

        # Step 5: Extract arrivals (from invalid-ET or fallback to historical trips)
        if et_data:
            print("Using invalid-ET data for arrivals.", file=sys.stderr)
            # Transform invalid-ET response into FaktiskAnkomst list
            faktiske = _parse_invalid_et_arrivals(et_data, dest_quay_ids)
        else:
            print("Falling back to historical trip data for arrivals.", file=sys.stderr)
            faktiske = extract_faktiske_ankomster(historical_data, dest_quay_ids)

        # Step 6: Delay statistics
        statistikk = compute_delay_statistics(faktiske, dest_name)

        # Step 7: Cancellations from current trips + quay data
        innstillinger = extract_innstillinger(current_data)
        for qdata in quay_results:
            innstillinger.extend(extract_innstillinger({"trip": {"tripPatterns": []}}, qdata))

        # Step 9: Car travel data
        bildata = None
        if osrm_result:
            print("Building car travel data...", file=sys.stderr)
            bildata = build_bildata(osrm_result, current_volumes, historical_avgs)

        # Step 10: Weather data
        vaerdata = build_vaerdata(weather_entry)

        # Step 11: Assemble
        return build_kontrakt_a(
            bruker, avvik, alternativer, faktiske, statistikk, innstillinger, bildata, vaerdata
        )


def _parse_invalid_et_arrivals(
    et_data: dict,
    destination_quay_ids: set[str],
) -> list:
    """Parse invalid-ET API response into FaktiskAnkomst records."""
    from data.models import FaktiskAnkomst
    from data.transform import _minutes_between

    arrivals = []
    for call in et_data.get("estimatedCalls", []):
        quay = call.get("quay") or {}
        if quay.get("id") not in destination_quay_ids:
            continue
        sj = call.get("serviceJourney") or {}
        line = sj.get("line") or {}
        aimed = call.get("aimedArrivalTime")
        actual = call.get("actualArrivalTime") or call.get("expectedArrivalTime")
        cancelled = call.get("cancellation", False)
        delay = _minutes_between(aimed, actual)

        arrivals.append({
            "service_journey_id": sj.get("id", ""),
            "linje": line.get("publicCode", ""),
            "planlagt_ankomst": aimed or "",
            "faktisk_ankomst": None if cancelled else (actual or ""),
            "forsinkelse_min": None if cancelled else delay,
            "innstilt": cancelled,
        })
    return arrivals


def main():
    parser = argparse.ArgumentParser(description="Pendlerkompis data layer")
    parser.add_argument(
        "--direction",
        choices=["fra_hjem", "fra_jobb"],
        default="fra_jobb",
        help="Travel direction (default: fra_jobb)",
    )
    parser.add_argument(
        "--time",
        default=None,
        help="Override departure time (HH:MM)",
    )
    args = parser.parse_args()

    result = asyncio.run(hent_pendlerdata(args.direction, args.time))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
