"""Data models matching Kontrakt A schema + extensions for the motor."""

from __future__ import annotations
from typing import TypedDict


class Koordinater(TypedDict):
    lat: float
    lon: float


class Sted(TypedDict):
    navn: str
    koordinater: Koordinater


class Avreisetider(TypedDict):
    fra_hjem: str  # "HH:MM"
    fra_jobb: str  # "HH:MM"


class LaertPreferanse(TypedDict):
    situasjon: str
    valgt_handling: str
    antall_ganger: int


class Preferanser(TypedDict):
    laert: list[LaertPreferanse]


class Bruker(TypedDict):
    id: str
    hjem: Sted
    jobb: Sted
    avreisetider: Avreisetider
    preferanser: Preferanser


class Avvik(TypedDict, total=False):
    id: str
    kilde: str  # "SIRI-SX" | "SIRI-ET" | "manuell"
    type: str
    alvorlighet: str  # "lav" | "middels" | "hoy"
    beskrivelse: str
    paavirker_linjer: list[str]
    paavirker_stasjoner: list[str]
    estimert_varighet_min: int
    oppstaat: str  # ISO-8601


class Steg(TypedDict, total=False):
    type: str  # "gange" | "tog" | "buss" | "trikk" | "tbane" | "ferje"
    linje: str
    fra: str
    til: str
    varighet_min: int


class Reisealternativ(TypedDict):
    id: str
    beskrivelse: str
    avgang: str  # ISO-8601
    estimert_ankomst: str  # ISO-8601
    steg: list[Steg]
    status: str  # "i_rute" | "forsinket" | "innstilt" | "ukjent"


# --- Extensions for the motor (supplementary to Kontrakt A) ---

class FaktiskAnkomst(TypedDict, total=False):
    service_journey_id: str
    linje: str
    planlagt_ankomst: str  # ISO-8601
    faktisk_ankomst: str | None  # ISO-8601, None if cancelled
    forsinkelse_min: float | None
    innstilt: bool


class ForsinkelsesStatistikk(TypedDict):
    linje: str
    stasjon: str
    time_paa_doegnet: int  # hour 0-23
    median_forsinkelse_min: float
    p90_forsinkelse_min: float
    antall_observasjoner: int


class Innstilling(TypedDict, total=False):
    service_journey_id: str
    linje: str
    type: str  # "hel_tur" | "delvis"
    paavirket_stasjon: str | None


class Sanntidsdata(TypedDict):
    faktiske_ankomster: list[FaktiskAnkomst]
    forsinkelsesstatistikk: list[ForsinkelsesStatistikk]
    innstillinger: list[Innstilling]


class TrafikkPunkt(TypedDict):
    stasjon: str
    volum_siste_time: int  # vehicles counted last hour
    volum_normalt: int  # typical volume same hour/weekday
    kapasitetsutnyttelse: float  # ratio: siste_time / normalt (>1 = busier than usual)


class Bildata(TypedDict, total=False):
    reisetid_fri_flyt_min: float  # OSRM free-flow travel time
    avstand_km: float  # OSRM distance
    trafikk_punkter: list[TrafikkPunkt]  # Vegvesen volume readings along route
    estimert_reisetid_min: float | None  # adjusted estimate (free-flow * congestion factor)
    kilde: str  # "osrm+vegvesen_trafikkdata"


class KontraktAUtvidet(TypedDict):
    bruker: Bruker
    avvik: list[Avvik]
    reisealternativer: list[Reisealternativ]
    sanntidsdata: Sanntidsdata
    bildata: Bildata
