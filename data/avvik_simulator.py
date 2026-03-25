"""Realistisk avvikssimulator for Drammen <-> Oslo-pendling.

Simulerer typiske avvik paa Vestfoldbanen/Drammenbanen med ~50 % sannsynlighet.
Naar et avvik injiseres, paavirkes ogsaa reisealternativer (forsinkelser, innstillinger)
og sanntidsdata (innstillinger, forsinkelsesstatistikk) slik at heile databildet
er konsistent.

Bruk:
    from data.avvik_simulator import injiser_avvik
    kontrakt_a = injiser_avvik(kontrakt_a)
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

CET = timezone(timedelta(hours=1))

# ---- Linjer og stasjoner paa Rolfs pendlerstrekning ----

LINJER_DRAMMEN_OSLO = ["RE11", "L1", "R11", "L12", "L13"]

STASJONER_DRAMMEN_OSLO = [
    "Drammen",
    "Brakeroeya",
    "Lier",
    "Asker",
    "Sandvika",
    "Lysaker",
    "Skoyen",
    "Nationaltheatret",
    "Oslo S",
]

# ---- Scenarioer — vektet med sannsynlighet ----
# Kvart scenario har:
#   weight        – relativ sannsynlighet (blant avvikstilfelle)
#   alvorlighet   – "lav" | "middels" | "hoy"
#   type          – fritekst avvikstype
#   mal           – f-string-mal for beskrivelse ({stasjon}, {linje}, {min})
#   varighet_min  – (min, max) for estimert varighet
#   linjer_n      – kor mange linjer som vert paavirka (min, max)
#   effekt        – korleis reisealternativ vert paavirka
#                   "innstilt" | "forsinket" | "delvis_innstilt" | "blanda"

SCENARIER = [
    {
        "weight": 15,
        "alvorlighet": "hoy",
        "type": "signalfeil",
        "mal": "Signalfeil ved {stasjon} stasjon. Togtrafikken er stengt i begge retningar.",
        "varighet_range": (30, 120),
        "linjer_n": (2, 4),
        "effekt": "innstilt",
    },
    {
        "weight": 10,
        "alvorlighet": "hoy",
        "type": "stroembrudd",
        "mal": "Stroembrudd paa kontaktleidningen mellom {stasjon} og {stasjon2}. Ingen togtrafikk paa strekninga.",
        "varighet_range": (45, 180),
        "linjer_n": (3, 5),
        "effekt": "innstilt",
    },
    {
        "weight": 8,
        "alvorlighet": "hoy",
        "type": "personpaakjoering",
        "mal": "Personpaakjoering ved {stasjon}. All togtrafikk gjennom {stasjon} er innstilt inntil vidare.",
        "varighet_range": (60, 240),
        "linjer_n": (3, 5),
        "effekt": "innstilt",
    },
    {
        "weight": 20,
        "alvorlighet": "middels",
        "type": "sporveksel",
        "mal": "Feil paa sporveksel ved {stasjon}. Toga vert spora om og faar {min} minutts forseinking.",
        "varighet_range": (20, 60),
        "linjer_n": (1, 3),
        "effekt": "forsinket",
    },
    {
        "weight": 15,
        "alvorlighet": "middels",
        "type": "infrastruktur",
        "mal": "Arbeid paa skinnene mellom {stasjon} og {stasjon2}. Redusert framkomst, {min} min ekstra reisetid.",
        "varighet_range": (30, 90),
        "linjer_n": (1, 3),
        "effekt": "forsinket",
    },
    {
        "weight": 12,
        "alvorlighet": "middels",
        "type": "materiellmangel",
        "mal": "Materiellmangel paa {linje}. Enkelte avgangar er innstilte, resten gaar med redusert kapasitet.",
        "varighet_range": (60, 240),
        "linjer_n": (1, 1),
        "effekt": "delvis_innstilt",
    },
    {
        "weight": 10,
        "alvorlighet": "lav",
        "type": "forsinkelse",
        "mal": "Forseinka tog paa {linje} pga. ventetid i Drammen. Ca. {min} min forseinking.",
        "varighet_range": (5, 20),
        "linjer_n": (1, 1),
        "effekt": "forsinket",
    },
    {
        "weight": 5,
        "alvorlighet": "hoy",
        "type": "vaer",
        "mal": "Kraftig snoefall foeerer til store forseiningar paa Drammenbanen. Fleire avgangar innstilte.",
        "varighet_range": (120, 480),
        "linjer_n": (3, 5),
        "effekt": "blanda",
    },
    {
        "weight": 5,
        "alvorlighet": "middels",
        "type": "uvedkommande_i_sporet",
        "mal": "Uvedkommande personar i sporet ved {stasjon}. Togtrafikken er midlertidig stansa.",
        "varighet_range": (15, 45),
        "linjer_n": (2, 4),
        "effekt": "innstilt",
    },
]


def _vel_scenario() -> dict:
    """Vel eit tilfeldig scenario, vekta etter weight."""
    weights = [s["weight"] for s in SCENARIER]
    return random.choices(SCENARIER, weights=weights, k=1)[0]


def _vel_stasjoner(n: int = 2) -> list[str]:
    """Vel n tilfeldige stasjoner, sortert i rute-rekkefoelge."""
    valgt = random.sample(STASJONER_DRAMMEN_OSLO, min(n, len(STASJONER_DRAMMEN_OSLO)))
    return sorted(valgt, key=lambda s: STASJONER_DRAMMEN_OSLO.index(s))


def _vel_linjer(n_range: tuple[int, int]) -> list[str]:
    n = random.randint(*n_range)
    return random.sample(LINJER_DRAMMEN_OSLO, min(n, len(LINJER_DRAMMEN_OSLO)))


def _bygg_avvik(scenario: dict, naa: datetime) -> dict:
    """Bygg eit Avvik-objekt fraa eit scenario."""
    stasjoner = _vel_stasjoner(3)
    linjer = _vel_linjer(scenario["linjer_n"])
    varighet = random.randint(*scenario["varighet_range"])

    # Avviket oppstod 5–45 min sidan
    oppstod_min = random.randint(5, 45)
    oppstaat = (naa - timedelta(minutes=oppstod_min)).isoformat()

    # Bygg beskrivelse
    beskrivelse = scenario["mal"].format(
        stasjon=stasjoner[0],
        stasjon2=stasjoner[1] if len(stasjoner) > 1 else stasjoner[0],
        linje=linjer[0],
        min=varighet,
    )

    return {
        "id": f"sim-{uuid.uuid4().hex[:8]}",
        "kilde": "SIRI-SX",
        "type": scenario["type"],
        "alvorlighet": scenario["alvorlighet"],
        "beskrivelse": beskrivelse,
        "paavirker_linjer": linjer,
        "paavirker_stasjoner": [stasjoner[0]] + ([stasjoner[1]] if len(stasjoner) > 1 else []),
        "estimert_varighet_min": varighet,
        "oppstaat": oppstaat,
    }


def _paavirk_alternativer(alternativer: list[dict], avvik: dict, effekt: str) -> list[dict]:
    """Juster status, avgangs-/ankomsttider og steg basert paa avvikseffekt.

    I røynda oppdaterer Entur Journey Planner expectedStartTime/expectedEndTime
    basert paa SIRI ET-data. Vi simulerer same oppfoeorsel:
    - Forseinka avgangar (avgang) naar toget ikkje kan koeyre i tide
    - Forseinka ankomst (estimert_ankomst) pga. lenger reisetid
    - Justerte steg-varigheiter for paavirka toglinjer
    - Innstilte ruter faar estimert_ankomst = null
    """
    paavirka_linjer = set(avvik.get("paavirker_linjer", []))
    paavirka_stasjoner = set(avvik.get("paavirker_stasjoner", []))
    oppdatert = []

    for alt in alternativer:
        alt = dict(alt)  # shallow copy
        steg_liste = [dict(s) for s in alt.get("steg", [])]
        alt_linjer = {s.get("linje", "") for s in steg_liste}

        if not alt_linjer & paavirka_linjer:
            oppdatert.append(alt)
            continue

        if effekt == "innstilt":
            alt["status"] = "innstilt"
            alt["estimert_ankomst"] = None
            alt["steg"] = steg_liste

        elif effekt == "forsinket":
            alt["status"] = "forsinket"
            forsinkelse = _berekn_forsinkelse(steg_liste, paavirka_linjer, paavirka_stasjoner, (8, 35))
            alt = _juster_tider(alt, steg_liste, forsinkelse)

        elif effekt == "delvis_innstilt":
            if random.random() < 0.4:
                alt["status"] = "innstilt"
                alt["estimert_ankomst"] = None
                alt["steg"] = steg_liste
            else:
                alt["status"] = "forsinket"
                forsinkelse = _berekn_forsinkelse(steg_liste, paavirka_linjer, paavirka_stasjoner, (5, 20))
                alt = _juster_tider(alt, steg_liste, forsinkelse)

        elif effekt == "blanda":
            if random.random() < 0.3:
                alt["status"] = "innstilt"
                alt["estimert_ankomst"] = None
                alt["steg"] = steg_liste
            else:
                alt["status"] = "forsinket"
                forsinkelse = _berekn_forsinkelse(steg_liste, paavirka_linjer, paavirka_stasjoner, (15, 60))
                alt = _juster_tider(alt, steg_liste, forsinkelse)

        oppdatert.append(alt)

    return oppdatert


def _berekn_forsinkelse(
    steg_liste: list[dict],
    paavirka_linjer: set[str],
    paavirka_stasjoner: set[str],
    delay_range: tuple[int, int],
) -> dict:
    """Berekn forsinkelse per steg basert paa kva linjer/stasjoner som er paavirka.

    Returnerer dict med:
      avgang_forsinkelse_min  – forseinking foer toget i det heile kan koeyre
      steg_forsinkelse        – liste med ekstra minutt per steg
      total_ekstra_min        – sum av all forseinking
    """
    base_delay = random.randint(*delay_range)

    # Avgangsforseinking: viss avviket er paa ein stasjon tidleg i ruta,
    # kan toget ikkje starte i tide
    avgang_forsinkelse = 0
    steg_forsinkelse = []

    for steg in steg_liste:
        linje = steg.get("linje", "")
        fra = steg.get("fra", "")
        til = steg.get("til", "")

        if linje in paavirka_linjer:
            # Sjekk om avviket er paa ein stasjon dette steget passerer
            stasjon_treff = fra in paavirka_stasjoner or til in paavirka_stasjoner

            if stasjon_treff:
                # Hovuddelen av forseinkinga legg seg paa dette steget
                ekstra = base_delay
            else:
                # Paavirka linje men ikkje direkte stasjon — fylgjeforseinking
                ekstra = random.randint(3, max(4, base_delay // 3))

            # Viss dette er foerste togsteg, kan avgangen verta forseinka
            if steg.get("type") == "tog" and avgang_forsinkelse == 0 and ekstra > 5:
                avgang_forsinkelse = random.randint(2, max(3, ekstra // 2))

            steg_forsinkelse.append(ekstra)
        else:
            steg_forsinkelse.append(0)

    total = avgang_forsinkelse + sum(steg_forsinkelse)
    return {
        "avgang_forsinkelse_min": avgang_forsinkelse,
        "steg_forsinkelse": steg_forsinkelse,
        "total_ekstra_min": total,
    }


def _juster_tider(alt: dict, steg_liste: list[dict], forsinkelse: dict) -> dict:
    """Juster avgang, ankomst og steg-varigheiter for eit forseinka alternativ."""
    avgang_delay = forsinkelse["avgang_forsinkelse_min"]
    steg_delays = forsinkelse["steg_forsinkelse"]
    total_delay = forsinkelse["total_ekstra_min"]

    # Juster avgang (expectedStartTime i Entur-verda)
    try:
        avgang = datetime.fromisoformat(alt["avgang"])
        alt["avgang"] = (avgang + timedelta(minutes=avgang_delay)).isoformat()
    except (ValueError, KeyError):
        pass

    # Juster estimert ankomst
    try:
        ankomst = datetime.fromisoformat(alt["estimert_ankomst"])
        alt["estimert_ankomst"] = (ankomst + timedelta(minutes=total_delay)).isoformat()
    except (ValueError, KeyError):
        pass

    # Juster varigheit paa kvart paavirka steg
    for i, steg in enumerate(steg_liste):
        if i < len(steg_delays) and steg_delays[i] > 0:
            steg["varighet_min"] = steg.get("varighet_min", 0) + steg_delays[i]
    alt["steg"] = steg_liste

    return alt


def _paavirk_sanntidsdata(sanntidsdata: dict, avvik: dict, effekt: str) -> dict:
    """Legg til konsistente innstillingar og forsinkelsesstatistikk."""
    sanntidsdata = dict(sanntidsdata)
    paavirka_linjer = avvik.get("paavirker_linjer", [])

    if effekt in ("innstilt", "delvis_innstilt", "blanda"):
        nye_innstillinger = []
        for linje in paavirka_linjer:
            if effekt == "delvis_innstilt" and random.random() > 0.5:
                continue
            nye_innstillinger.append({
                "service_journey_id": f"sim-sj-{uuid.uuid4().hex[:6]}",
                "linje": linje,
                "type": "hel_tur",
                "paavirket_stasjon": None,
            })
        sanntidsdata["innstillinger"] = sanntidsdata.get("innstillinger", []) + nye_innstillinger

    # Legg til forhoega p90 i statistikk for paavirka linjer
    eksisterande = {s["linje"] for s in sanntidsdata.get("forsinkelsesstatistikk", [])}
    for linje in paavirka_linjer:
        if linje not in eksisterande:
            naa = datetime.now(CET)
            sanntidsdata.setdefault("forsinkelsesstatistikk", []).append({
                "linje": linje,
                "stasjon": "Drammen",
                "time_paa_doegnet": naa.hour,
                "median_forsinkelse_min": round(random.uniform(5, 15), 1),
                "p90_forsinkelse_min": round(random.uniform(15, 40), 1),
                "antall_observasjoner": random.randint(3, 8),
            })

    return sanntidsdata


def injiser_avvik(
    kontrakt_a: dict,
    sannsynlighet: float = 0.5,
    tving_avvik: bool | None = None,
) -> dict:
    """Injiser simulerte avvik i ein ferdig Kontrakt A med ~50 % sannsynlighet.

    Args:
        kontrakt_a: Ferdig Kontrakt A fraa data-laget.
        sannsynlighet: Sjansen for at det vert lagt inn avvik (0.0–1.0).
        tving_avvik: True = alltid avvik, False = aldri, None = bruk sannsynlighet.

    Returns:
        Oppdatert Kontrakt A (same objekt, mutert).
    """
    # Avgjerd: skal vi injisere?
    if tving_avvik is True:
        skal_injisere = True
    elif tving_avvik is False:
        skal_injisere = False
    else:
        skal_injisere = random.random() < sannsynlighet

    if not skal_injisere:
        return kontrakt_a

    naa = datetime.now(CET)
    scenario = _vel_scenario()
    avvik_obj = _bygg_avvik(scenario, naa)

    # Injiser avviket
    kontrakt_a["avvik"] = kontrakt_a.get("avvik", []) + [avvik_obj]

    # Paavirk reisealternativ konsistent
    kontrakt_a["reisealternativer"] = _paavirk_alternativer(
        kontrakt_a.get("reisealternativer", []),
        avvik_obj,
        scenario["effekt"],
    )

    # Paavirk sanntidsdata konsistent
    if "sanntidsdata" in kontrakt_a:
        kontrakt_a["sanntidsdata"] = _paavirk_sanntidsdata(
            kontrakt_a["sanntidsdata"],
            avvik_obj,
            scenario["effekt"],
        )

    return kontrakt_a
