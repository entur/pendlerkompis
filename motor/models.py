"""Kontrakt B datamodeller (Motor -> Presentasjon)."""

from typing import TypedDict


class Situasjon(TypedDict, total=False):
    oppsummering: str
    alvorlighet: str  # "ingen", "lav", "middels", "hoy"
    avvik_ids: list[str]


class Alternativ(TypedDict, total=False):
    handling: str  # "reis_som_normalt", "reis_tidligere", "utsett", "alternativ_rute", "ikke_reis"
    beskrivelse: str
    alternativ_id: str | None
    estimert_ankomst_hjem: str | None


class KontraktB(TypedDict, total=False):
    bruker_id: str
    type: str  # "avvik", "vaermelding"
    tidspunkt: str
    situasjon: Situasjon
    anbefaling: Alternativ
    andre_alternativer: list[Alternativ]
