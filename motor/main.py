"""Motor: Orkestrer data -> klassifiser -> ranger -> tekst -> Kontrakt B."""

import argparse
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from data.avvik_simulator import injiser_avvik
from data.main import hent_pendlerdata
from motor.klassifiser import klassifiser
from motor.models import KontraktB
from motor.ranger import ranger
from motor.tekst import generer_tekst


async def analyser(direction: str = "fra_jobb", override_time: str | None = None) -> KontraktB:
    """Hovudflyt: hent data, analyser, lever Kontrakt B."""

    # 1. Hent Kontrakt A fraa data-laget
    kontrakt_a = await hent_pendlerdata(direction=direction, override_time=override_time)

    # 1b. Simuler avvik (~50 % av kall) for demo/testing
    kontrakt_a = injiser_avvik(kontrakt_a)

    # 2. Klassifiser situasjonen
    type_, alvorlighet = klassifiser(kontrakt_a)

    # 3. Ranger alternativer og vel anbefaling
    anbefaling, andre = ranger(kontrakt_a, type_)

    # 4. Generer tekst (Claude API for avvik, malar for vaermelding)
    oppsummering, anbefaling_tekst = await generer_tekst(
        kontrakt_a, type_, alvorlighet, anbefaling, andre
    )

    # Oppdater anbefaling med generert tekst
    anbefaling["beskrivelse"] = anbefaling_tekst

    # 5. Bygg Kontrakt B
    naa = datetime.now(timezone(timedelta(hours=1)))

    kontrakt_b: KontraktB = {
        "bruker_id": kontrakt_a.get("bruker", {}).get("id", "ukjent"),
        "type": type_,
        "tidspunkt": naa.isoformat(),
        "situasjon": {
            "oppsummering": oppsummering,
            "alvorlighet": alvorlighet,
            "avvik_ids": [a["id"] for a in kontrakt_a.get("avvik", [])],
        },
        "anbefaling": anbefaling,
        "andre_alternativer": andre,
    }

    return kontrakt_b


def main():
    parser = argparse.ArgumentParser(description="Pendlerkompis Motor")
    parser.add_argument(
        "--direction",
        choices=["fra_hjem", "fra_jobb"],
        default="fra_jobb",
        help="Reiseretning (default: fra_jobb)",
    )
    parser.add_argument(
        "--time",
        default=None,
        help="Overstyr avreisetid (HH:MM)",
    )
    args = parser.parse_args()

    result = asyncio.run(analyser(direction=args.direction, override_time=args.time))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
