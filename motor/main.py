"""Pendlerkompis motor — analyse og anbefaling.

Henter data fra datalaget, sender til Claude og returnerer Kontrakt B.

Bruk:
    cd pendlerkompis
    PYTHONPATH=. python -m motor.main --direction fra_jobb
    PYTHONPATH=. python -m motor.main --direction fra_hjem --time 07:15
    PYTHONPATH=. python -m motor.main --mock   # bruk mock-data (uten API-kall)

Lokal OTP (second-otp på localhost:8081):
    JOURNEY_PLANNER_URL=http://localhost:8081/otp/transmodel/v3 python -m motor.main
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

CET = timezone(timedelta(hours=1))


def _has_disruption(kontrakt_a: dict) -> bool:
    innstillinger = kontrakt_a.get("sanntidsdata", {}).get("innstillinger", [])
    return bool(innstillinger) or bool(kontrakt_a.get("avvik"))


def _build_normal_response(kontrakt_a: dict) -> dict:
    """Quick Kontrakt B when there are no disruptions — no Claude call needed."""
    alts = kontrakt_a.get("reisealternativer", [])
    bruker = kontrakt_a.get("bruker", {})

    def _alt(a):
        return {
            "handling": "reis_som_normalt",
            "beskrivelse": a.get("beskrivelse", ""),
            "alternativ_id": a.get("id"),
            "estimert_ankomst_hjem": a.get("estimert_ankomst"),
        }

    first = alts[0] if alts else {}
    return {
        "bruker_id": bruker.get("id", "rolf-1"),
        "type": "normal",
        "tidspunkt": datetime.now(tz=CET).isoformat(),
        "situasjon": {
            "oppsummering": "Ingen avvik — reisen går som normalt.",
            "alvorlighet": "ingen",
            "avvik_ids": [],
        },
        "anbefaling": {
            "handling": "reis_som_normalt",
            "beskrivelse": first.get("beskrivelse", ""),
            "alternativ_id": first.get("id"),
            "estimert_ankomst_hjem": first.get("estimert_ankomst"),
        },
        "andre_alternativer": [_alt(a) for a in alts[1:4]],
    }


async def generate_recommendation_smart(
    direction: str = "fra_jobb",
    override_time: str | None = None,
    verbose: bool = False,
) -> dict:
    """Fetch data, skip Claude if no disruption, invoke Claude only when needed."""
    from data.main import hent_pendlerdata
    from motor.prompt import build_prompt
    from motor.claude_client import call_claude

    if verbose:
        print(f"[motor] Henter pendlerdata (retning={direction})...", file=sys.stderr)

    kontrakt_a = await hent_pendlerdata(direction, override_time)

    if not _has_disruption(kontrakt_a):
        if verbose:
            print("[motor] Ingen avvik — returnerer normal respons uten Claude.", file=sys.stderr)
        return _build_normal_response(kontrakt_a)

    if verbose:
        innstillinger = kontrakt_a.get("innstillinger", [])
        avvik = kontrakt_a.get("avvik", [])
        print(
            f"[motor] Avvik oppdaget ({len(innstillinger)} innstillinger, "
            f"{len(avvik)} situasjoner) — sender til Claude...",
            file=sys.stderr,
        )

    prompt = build_prompt(kontrakt_a)
    return call_claude(prompt, verbose=verbose)


async def generate_recommendation(
    direction: str = "fra_jobb",
    override_time: str | None = None,
    verbose: bool = False,
) -> dict:
    """Hovedfunksjon: henter data og genererer Kontrakt B.

    Args:
        direction: "fra_jobb" eller "fra_hjem"
        override_time: override avreisetid (HH:MM), None = bruk profil
        verbose: logg fremgang til stderr

    Returns:
        dict — Kontrakt B (situasjon + anbefaling + alternativer)
    """
    from data.main import hent_pendlerdata
    from motor.prompt import build_prompt
    from motor.claude_client import call_claude

    if verbose:
        print(f"[motor] Henter pendlerdata (retning={direction})...", file=sys.stderr)

    kontrakt_a = await hent_pendlerdata(direction, override_time)

    prompt = build_prompt(kontrakt_a)
    kontrakt_b = call_claude(prompt, verbose=verbose)

    return kontrakt_b


async def generate_recommendation_from_mock(verbose: bool = False) -> dict:
    """Generer anbefaling fra mock Kontrakt A (uten API-kall)."""
    from motor.prompt import build_prompt
    from motor.claude_client import call_claude

    mock_path = Path(__file__).parent.parent / "shared" / "mock-kontrakt-a.json"
    kontrakt_a = json.loads(mock_path.read_text(encoding="utf-8"))

    if verbose:
        print("[motor] Bruker mock-data fra shared/mock-kontrakt-a.json", file=sys.stderr)

    prompt = build_prompt(kontrakt_a)
    kontrakt_b = call_claude(prompt, verbose=verbose)

    return kontrakt_b


def main():
    parser = argparse.ArgumentParser(description="Pendlerkompis motor")
    parser.add_argument(
        "--direction",
        choices=["fra_hjem", "fra_jobb"],
        default="fra_jobb",
    )
    parser.add_argument("--time", default=None, help="Override avreisetid (HH:MM)")
    parser.add_argument("--mock", action="store_true", help="Bruk mock-data")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.mock:
        result = asyncio.run(generate_recommendation_from_mock(verbose=args.verbose))
    else:
        result = asyncio.run(
            generate_recommendation(args.direction, args.time, verbose=args.verbose)
        )

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
