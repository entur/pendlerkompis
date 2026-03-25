"""Transform Entur API responses into Kontrakt A format."""

from __future__ import annotations

import statistics
from datetime import datetime

from data.models import (
    Avvik,
    Bruker,
    FaktiskAnkomst,
    ForsinkelsesStatistikk,
    Innstilling,
    KontraktAUtvidet,
    Reisealternativ,
    Sanntidsdata,
    Steg,
)

# --- Mapping tables ---

MODE_MAP: dict[str, str] = {
    "foot": "gange",
    "rail": "tog",
    "bus": "buss",
    "tram": "trikk",
    "metro": "tbane",
    "water": "ferje",
}

SEVERITY_MAP: dict[str, str] = {
    "normal": "lav",
    "slight": "lav",
    "noImpact": "lav",
    "severe": "middels",
    "verySevere": "hoy",
    "undefined": "hoy",
}


# --- Trip response -> Avvik + Reisealternativer ---

def _minutes_between(iso_a: str | None, iso_b: str | None) -> float | None:
    """Return minutes between two ISO-8601 timestamps, or None."""
    if not iso_a or not iso_b:
        return None
    try:
        a = datetime.fromisoformat(iso_a)
        b = datetime.fromisoformat(iso_b)
        return (b - a).total_seconds() / 60
    except (ValueError, TypeError):
        return None


def _determine_status(legs: list[dict]) -> str:
    """Determine overall trip status from its legs."""
    any_cancelled = False
    any_delayed = False
    for leg in legs:
        if leg.get("mode") == "foot":
            continue
        to_call = leg.get("toEstimatedCall") or {}
        from_call = leg.get("fromEstimatedCall") or {}
        if to_call.get("cancellation") or from_call.get("cancellation"):
            any_cancelled = True
        delay = _minutes_between(
            to_call.get("aimedArrivalTime"), to_call.get("expectedArrivalTime")
        )
        if delay is not None and delay > 3:
            any_delayed = True
    if any_cancelled:
        return "innstilt"
    if any_delayed:
        return "forsinket"
    return "i_rute"


def _leg_to_steg(leg: dict) -> Steg:
    mode = MODE_MAP.get(leg.get("mode", ""), leg.get("mode", "gange"))
    steg: Steg = {
        "type": mode,
        "fra": leg.get("fromPlace", {}).get("name", ""),
        "til": leg.get("toPlace", {}).get("name", ""),
        "varighet_min": round((leg.get("duration") or 0) / 60),
    }
    line = leg.get("line")
    if line and line.get("publicCode"):
        steg["linje"] = line["publicCode"]
    return steg


def _build_beskrivelse(trip_pattern: dict) -> str:
    """Build a human-readable description from the trip pattern legs."""
    parts = []
    for leg in trip_pattern.get("legs", []):
        if leg.get("mode") == "foot":
            continue
        line = leg.get("line") or {}
        code = line.get("publicCode") or line.get("name") or ""
        mode = MODE_MAP.get(leg.get("mode", ""), leg.get("mode", ""))
        to_name = leg.get("toPlace", {}).get("name", "")
        parts.append(f"{mode.capitalize()} {code} til {to_name}")
    if not parts:
        return "Gange"
    return ", ".join(parts)


def transform_trip_pattern(trip_pattern: dict, index: int) -> Reisealternativ:
    legs = trip_pattern.get("legs", [])
    return {
        "id": f"alt-{index + 1}",
        "beskrivelse": _build_beskrivelse(trip_pattern),
        "avgang": trip_pattern.get("expectedStartTime", ""),
        "estimert_ankomst": trip_pattern.get("expectedEndTime", ""),
        "steg": [_leg_to_steg(leg) for leg in legs],
        "status": _determine_status(legs),
    }


def transform_situations(trip_data: dict) -> list[Avvik]:
    """Extract unique situations from all trip patterns into Avvik list."""
    seen_ids: set[str] = set()
    avvik_list: list[Avvik] = []

    for pattern in trip_data.get("trip", {}).get("tripPatterns", []):
        for leg in pattern.get("legs", []):
            for sit in leg.get("situations", []):
                sit_id = sit.get("id") or sit.get("situationNumber") or ""
                if sit_id in seen_ids:
                    continue
                seen_ids.add(sit_id)

                # Extract affected lines and stations
                linjer = []
                stasjoner = []
                for affect in sit.get("affects", []):
                    line = affect.get("line")
                    if line:
                        linjer.append(line.get("publicCode") or line.get("id", ""))
                    stop = affect.get("stopPlace")
                    if stop:
                        stasjoner.append(stop.get("name") or stop.get("id", ""))

                # Also tag from the leg's own line if not already included
                leg_line = leg.get("line", {})
                if leg_line.get("publicCode") and leg_line["publicCode"] not in linjer:
                    linjer.append(leg_line["publicCode"])

                summary = ""
                for s in sit.get("summary", []) if isinstance(sit.get("summary"), list) else [sit.get("summary", {})]:
                    if s and s.get("value"):
                        summary = s["value"]
                        break
                description = ""
                for d in sit.get("description", []) if isinstance(sit.get("description"), list) else [sit.get("description", {})]:
                    if d and d.get("value"):
                        description = d["value"]
                        break

                severity_raw = sit.get("severity", "undefined")
                validity = sit.get("validityPeriod") or {}

                avvik: Avvik = {
                    "id": sit_id,
                    "kilde": "SIRI-SX",
                    "type": sit.get("reportType", "general"),
                    "alvorlighet": SEVERITY_MAP.get(severity_raw, "lav"),
                    "beskrivelse": description or summary or "Ukjent avvik",
                    "paavirker_linjer": linjer,
                    "paavirker_stasjoner": stasjoner,
                }
                if validity.get("startTime"):
                    avvik["oppstaat"] = validity["startTime"]

                avvik_list.append(avvik)

    return avvik_list


def transform_trip_response(trip_data: dict) -> tuple[list[Avvik], list[Reisealternativ]]:
    """Transform a full Journey Planner trip response."""
    patterns = trip_data.get("trip", {}).get("tripPatterns", [])
    alternativer = [transform_trip_pattern(p, i) for i, p in enumerate(patterns)]
    avvik = transform_situations(trip_data)
    return avvik, alternativer


# --- Extract metadata from trip response ---

def extract_destination_quay_ids(trip_data: dict) -> set[str]:
    """Extract unique destination quay IDs from trip patterns (last non-foot leg)."""
    quay_ids: set[str] = set()
    for pattern in trip_data.get("trip", {}).get("tripPatterns", []):
        legs = pattern.get("legs", [])
        for leg in reversed(legs):
            if leg.get("mode") != "foot":
                quay = leg.get("toPlace", {}).get("quay") or {}
                if quay.get("id"):
                    quay_ids.add(quay["id"])
                break
    return quay_ids


def extract_line_codes(trip_data: dict) -> set[str]:
    """Extract unique line public codes from trip patterns."""
    codes: set[str] = set()
    for pattern in trip_data.get("trip", {}).get("tripPatterns", []):
        for leg in pattern.get("legs", []):
            line = leg.get("line") or {}
            if line.get("publicCode"):
                codes.add(line["publicCode"])
    return codes


def extract_service_journey_ids(trip_data: dict) -> list[str]:
    """Extract all serviceJourney IDs from trip patterns."""
    ids: list[str] = []
    for pattern in trip_data.get("trip", {}).get("tripPatterns", []):
        for leg in pattern.get("legs", []):
            sj = leg.get("serviceJourney") or {}
            if sj.get("id"):
                ids.append(sj["id"])
    return ids


# --- Historical/realtime data -> extended fields ---

def extract_faktiske_ankomster(
    historical_trip_data: dict,
    destination_quay_ids: set[str],
) -> list[FaktiskAnkomst]:
    """Extract arrival records from historical trip data at destination stops."""
    arrivals: list[FaktiskAnkomst] = []
    for pattern in historical_trip_data.get("trip", {}).get("tripPatterns", []):
        for leg in pattern.get("legs", []):
            if leg.get("mode") == "foot":
                continue
            to_quay = leg.get("toPlace", {}).get("quay") or {}
            if to_quay.get("id") not in destination_quay_ids:
                continue

            to_call = leg.get("toEstimatedCall") or {}
            line = leg.get("line") or {}
            sj = leg.get("serviceJourney") or {}

            aimed = to_call.get("aimedArrivalTime")
            expected = to_call.get("expectedArrivalTime")
            cancelled = to_call.get("cancellation", False)

            delay = _minutes_between(aimed, expected)

            arrivals.append({
                "service_journey_id": sj.get("id", ""),
                "linje": line.get("publicCode", ""),
                "planlagt_ankomst": aimed or "",
                "faktisk_ankomst": None if cancelled else (expected or ""),
                "forsinkelse_min": None if cancelled else delay,
                "innstilt": cancelled,
            })
    return arrivals


def compute_delay_statistics(
    faktiske_ankomster: list[FaktiskAnkomst],
    destination_name: str,
) -> list[ForsinkelsesStatistikk]:
    """Compute median and p90 delays grouped by line and hour of day."""
    from collections import defaultdict

    groups: dict[tuple[str, int], list[float]] = defaultdict(list)
    for fa in faktiske_ankomster:
        if fa.get("innstilt") or fa.get("forsinkelse_min") is None:
            continue
        try:
            hour = datetime.fromisoformat(fa["planlagt_ankomst"]).hour
        except (ValueError, KeyError):
            continue
        key = (fa.get("linje", ""), hour)
        groups[key].append(fa["forsinkelse_min"])

    stats: list[ForsinkelsesStatistikk] = []
    for (linje, hour), delays in sorted(groups.items()):
        if not delays:
            continue
        sorted_delays = sorted(delays)
        p90_idx = max(0, int(len(sorted_delays) * 0.9) - 1)
        stats.append({
            "linje": linje,
            "stasjon": destination_name,
            "time_paa_doegnet": hour,
            "median_forsinkelse_min": round(statistics.median(sorted_delays), 1),
            "p90_forsinkelse_min": round(sorted_delays[p90_idx], 1),
            "antall_observasjoner": len(sorted_delays),
        })
    return stats


def extract_innstillinger(
    trip_data: dict,
    quay_data: dict | None = None,
) -> list[Innstilling]:
    """Extract cancellations from current trip data and quay departures."""
    innstillinger: list[Innstilling] = []

    # From trip patterns
    for pattern in trip_data.get("trip", {}).get("tripPatterns", []):
        for leg in pattern.get("legs", []):
            if leg.get("mode") == "foot":
                continue
            from_call = leg.get("fromEstimatedCall") or {}
            to_call = leg.get("toEstimatedCall") or {}
            line = leg.get("line") or {}
            sj = leg.get("serviceJourney") or {}

            if from_call.get("cancellation") or to_call.get("cancellation"):
                stop_level = bool(to_call.get("cancellation")) and not bool(from_call.get("cancellation"))
                innstillinger.append({
                    "service_journey_id": sj.get("id", ""),
                    "linje": line.get("publicCode", ""),
                    "type": "delvis" if stop_level else "hel_tur",
                    "paavirket_stasjon": leg.get("toPlace", {}).get("name") if stop_level else None,
                })

    # From quay departure board
    if quay_data and quay_data.get("quay"):
        for call in quay_data["quay"].get("estimatedCalls", []):
            if call.get("cancellation"):
                sj = call.get("serviceJourney") or {}
                line = sj.get("line") or {}
                innstillinger.append({
                    "service_journey_id": sj.get("id", ""),
                    "linje": line.get("publicCode", ""),
                    "type": "hel_tur",
                    "paavirket_stasjon": quay_data["quay"].get("name"),
                })

    return innstillinger


# --- Assemble final output ---

def build_kontrakt_a(
    bruker: Bruker,
    avvik: list[Avvik],
    reisealternativer: list[Reisealternativ],
    faktiske_ankomster: list[FaktiskAnkomst],
    forsinkelsesstatistikk: list[ForsinkelsesStatistikk],
    innstillinger: list[Innstilling],
) -> KontraktAUtvidet:
    return {
        "bruker": bruker,
        "avvik": avvik,
        "reisealternativer": reisealternativer,
        "sanntidsdata": {
            "faktiske_ankomster": faktiske_ankomster,
            "forsinkelsesstatistikk": forsinkelsesstatistikk,
            "innstillinger": innstillinger,
        },
    }
