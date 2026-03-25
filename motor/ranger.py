"""Steg 3: Ranger alternativer og vel anbefaling."""

from motor.models import Alternativ


def ranger(kontrakt_a: dict, type_: str) -> tuple[Alternativ, list[Alternativ]]:
    """Ranger reisealternativ og vel ein anbefaling.

    Returns:
        (anbefaling, andre_alternativer)
    """
    alternativer = kontrakt_a.get("reisealternativer", [])
    laert = kontrakt_a.get("bruker", {}).get("preferanser", {}).get("laert", [])
    bildata = kontrakt_a.get("bildata")

    # Filtrer ut innstilte
    gyldige = [a for a in alternativer if a.get("status") != "innstilt"]
    innstilte = [a for a in alternativer if a.get("status") == "innstilt"]

    # Sorter paa estimert ankomst
    gyldige.sort(key=lambda a: a.get("estimert_ankomst", ""))

    if type_ == "avvik":
        # Boost basert paa laerte preferansar
        for alt in gyldige:
            handling = _gjett_handling(alt, gyldige)
            boost = _berekn_boost(handling, laert)
            alt["_boost"] = boost

        # Legg til bil viss relevant
        if bildata and _skal_foreslaa_bil(bildata, gyldige):
            gyldige.append(_bygg_bil_alternativ(bildata))

        # Re-sorter: tidlegaste ankomst, men boost tel
        gyldige.sort(key=lambda a: (a.get("estimert_ankomst", ""), -a.get("_boost", 0)))

    # Rydd opp interne felt
    for alt in gyldige:
        alt.pop("_boost", None)

    if not gyldige:
        # Alle innstilt — foreslaa bil eller ikkje reis
        if bildata:
            anbefaling = _bygg_bil_alternativ(bildata)
        else:
            anbefaling: Alternativ = {
                "handling": "ikke_reis",
                "beskrivelse": "Alle togavgangar er innstilt.",
                "alternativ_id": None,
                "estimert_ankomst_hjem": None,
            }
        return anbefaling, []

    # Topp-1 er anbefaling, resten er alternativ
    topp = gyldige[0]
    anbefaling = _bygg_alternativ(topp, gyldige, type_)
    andre = [_bygg_alternativ(a, gyldige, type_) for a in gyldige[1:]]

    # Legg til "ikkje reis" som siste alternativ ved avvik
    if type_ == "avvik":
        andre.append({
            "handling": "ikke_reis",
            "beskrivelse": "Jobb heimanfraa i dag",
            "alternativ_id": None,
            "estimert_ankomst_hjem": None,
        })

    return anbefaling, andre


def _gjett_handling(alt: dict, alle: list[dict]) -> str:
    """Gjett kva handling eit alternativ representerer."""
    if not alle:
        return "reis_som_normalt"

    # Tidlegaste avgang = reis_tidlegare
    tidlegaste = min(alle, key=lambda a: a.get("avgang", ""))
    if alt.get("avgang") == tidlegaste.get("avgang") and alt is tidlegaste:
        return "reis_tidligere"

    # Blanda transportmiddel = alternativ_rute
    typar = {s.get("type") for s in alt.get("steg", []) if s.get("type") != "gange"}
    if len(typar) > 1:
        return "alternativ_rute"

    return "utsett"


def _berekn_boost(handling: str, laert: list[dict]) -> int:
    """Berekn boost-score basert paa laerte preferansar."""
    for pref in laert:
        if pref.get("valgt_handling") == handling:
            return pref.get("antall_ganger", 0)
    return 0


def _skal_foreslaa_bil(bildata: dict, gyldige: list[dict]) -> bool:
    """Vurder om bil boer forslaast som alternativ."""
    bil_min = bildata.get("estimert_reisetid_min", 999)

    # Alle innstilt eller ingen gyldige
    if not gyldige:
        return True

    # Bil er vesentleg raskare enn beste togalternativ
    beste_tog_ankomst = gyldige[0].get("estimert_ankomst", "")
    beste_tog_avgang = gyldige[0].get("avgang", "")
    if beste_tog_ankomst and beste_tog_avgang:
        from datetime import datetime

        try:
            avgang = datetime.fromisoformat(beste_tog_avgang)
            ankomst = datetime.fromisoformat(beste_tog_ankomst)
            tog_min = (ankomst - avgang).total_seconds() / 60
            if bil_min < tog_min - 15:
                return True
        except (ValueError, TypeError):
            pass

    # Hoeg kapasitetsutnytting = ikkje foreslaa bil
    trafikk = bildata.get("trafikk_punkter", [])
    snitt_kapasitet = (
        sum(p.get("kapasitetsutnyttelse", 1.0) for p in trafikk) / len(trafikk) if trafikk else 1.0
    )
    if snitt_kapasitet > 1.5:
        return False

    return False


def _bygg_bil_alternativ(bildata: dict) -> dict:
    """Bygg eit reisealternativ for bil."""
    reisetid = bildata.get("estimert_reisetid_min", bildata.get("reisetid_fri_flyt_min", 0))
    avstand = bildata.get("avstand_km", 0)

    from datetime import datetime, timedelta, timezone

    naa = datetime.now(timezone(timedelta(hours=1)))
    ankomst = naa + timedelta(minutes=reisetid)

    return {
        "handling": "alternativ_rute",
        "beskrivelse": f"Kjoer bil via E18 — ca. {reisetid:.0f} min ({avstand:.0f} km)",
        "alternativ_id": None,
        "estimert_ankomst_hjem": ankomst.isoformat(),
        "_boost": 0,
    }


def _bygg_alternativ(alt: dict, alle: list[dict], type_: str) -> Alternativ:
    """Bygg Kontrakt B-alternativ fraa eit reisealternativ."""
    handling = _gjett_handling(alt, alle) if type_ == "avvik" else "reis_som_normalt"

    return {
        "handling": handling,
        "beskrivelse": alt.get("beskrivelse", ""),
        "alternativ_id": alt.get("id"),
        "estimert_ankomst_hjem": alt.get("estimert_ankomst"),
    }
