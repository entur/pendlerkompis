"""Steg 1: Klassifiser situasjonen som avvik eller vaermelding."""


def klassifiser(kontrakt_a: dict) -> tuple[str, str]:
    """Klassifiser situasjonen basert paa data i Kontrakt A.

    Returns:
        (type, alvorlighet) — f.eks. ("avvik", "hoy") eller ("vaermelding", "ingen")
    """
    avvik = kontrakt_a.get("avvik", [])
    alternativer = kontrakt_a.get("reisealternativer", [])
    sanntid = kontrakt_a.get("sanntidsdata", {})
    innstillinger = sanntid.get("innstillinger", [])
    stats = sanntid.get("forsinkelsesstatistikk", [])

    # Hoey prioritet: aktive avvik fraa SIRI-SX
    if avvik:
        alvorlighet = _hoeyeste_alvorlighet(avvik)
        return "avvik", alvorlighet

    # Hoey prioritet: innstilling paa brukarens linjer
    bruker_linjer = _extract_linjer(alternativer)
    if any(i.get("linje") in bruker_linjer for i in innstillinger):
        return "avvik", "hoy"

    # Middels prioritet: forsinka alternativ
    forsinkede = [a for a in alternativer if a.get("status") == "forsinket"]
    if forsinkede:
        return "avvik", "middels"

    # Lav prioritet: historisk upaalitelegheit (p90 > 10 min)
    hoey_p90 = [s for s in stats if s.get("p90_forsinkelse_min", 0) > 10]
    if hoey_p90:
        return "vaermelding", "lav"

    return "vaermelding", "ingen"


ALVORLIGHET_RANG = {"hoy": 3, "middels": 2, "lav": 1}


def _hoeyeste_alvorlighet(avvik: list[dict]) -> str:
    """Returner hoeyeste alvorlegheit fraa ei liste avvik."""
    if not avvik:
        return "lav"
    return max(avvik, key=lambda a: ALVORLIGHET_RANG.get(a.get("alvorlighet", "lav"), 0)).get(
        "alvorlighet", "lav"
    )


def _extract_linjer(alternativer: list[dict]) -> set[str]:
    """Hent alle linjekodar fraa reisealternativa."""
    linjer = set()
    for alt in alternativer:
        for steg in alt.get("steg", []):
            if linje := steg.get("linje"):
                linjer.add(linje)
    return linjer
