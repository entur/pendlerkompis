"""Steg 4: Generer tekst — Claude API for avvik, malar for vaermelding."""

import os

import anthropic


VAERMELDING_MALAR = {
    "ingen": "Heimreisa ser bra ut. {linje} kl {tid} er i rute.",
    "lav": (
        "Heimreisa ser bra ut, men {linje} har vore noko forseinka i dag "
        "(p90: {p90} min). {linje} kl {tid} er i rute no."
    ),
}


def _finn_tog_avgang(alt: dict) -> str:
    """Finn togets avgangstid fraa steg-data (ikkje trip-start med gangdel).

    Journey Planner returnerer expectedStartTime for heile trippen,
    som inkluderer gange til stasjonen. Vi treng togets faktiske
    avgangstid for aa vise korrekt klokkeslett til brukaren.
    """
    avgang_iso = alt.get("avgang", "")
    if not avgang_iso or "T" not in avgang_iso:
        return ""

    from datetime import datetime, timedelta

    try:
        trip_start = datetime.fromisoformat(avgang_iso)
    except (ValueError, TypeError):
        return ""

    # Summar gangminutta foer foerste transportleg
    gange_min = 0
    for steg in alt.get("steg", []):
        if steg.get("type") == "gange":
            gange_min += steg.get("varighet_min", 0)
        else:
            break

    tog_avgang = trip_start + timedelta(minutes=gange_min)
    return tog_avgang.strftime("%H:%M")


async def generer_tekst(
    kontrakt_a: dict,
    type_: str,
    alvorlighet: str,
    anbefaling: dict,
    andre: list[dict],
) -> tuple[str, str]:
    """Generer oppsummering og anbefalingstekst.

    Returns:
        (oppsummering, anbefaling_beskrivelse)
    """
    if type_ == "vaermelding":
        return _generer_vaermelding(kontrakt_a, alvorlighet, anbefaling)

    return await _generer_avvikstekst(kontrakt_a, anbefaling, andre)


def _generer_vaermelding(
    kontrakt_a: dict, alvorlighet: str, anbefaling: dict
) -> tuple[str, str]:
    """Generer vaermelding fraa mal — ingen API-kall."""
    # Finn linje og tid fraa anbefalinga
    alt_id = anbefaling.get("alternativ_id")
    linje = ""
    tid = ""

    for alt in kontrakt_a.get("reisealternativer", []):
        if alt.get("id") == alt_id:
            for steg in alt.get("steg", []):
                if steg.get("linje"):
                    linje = steg["linje"]
                    break
            # Finn togets avgangstid (ikkje trip-start som inkluderer gange)
            tid = _finn_tog_avgang(alt)
            break

    # Finn p90 for malen
    stats = kontrakt_a.get("sanntidsdata", {}).get("forsinkelsesstatistikk", [])
    p90 = 0
    for s in stats:
        if s.get("linje") == linje:
            p90 = max(p90, s.get("p90_forsinkelse_min", 0))

    mal = VAERMELDING_MALAR.get(alvorlighet, VAERMELDING_MALAR["ingen"])
    oppsummering = mal.format(linje=linje or "Toget", tid=tid or "neste avgang", p90=f"{p90:.0f}")

    beskrivelse = f"Ta {linje} kl {tid} som vanleg." if linje and tid else anbefaling.get("beskrivelse", "")

    return oppsummering, beskrivelse


async def _generer_avvikstekst(
    kontrakt_a: dict,
    anbefaling: dict,
    andre: list[dict],
) -> tuple[str, str]:
    """Generer avvikstekst via Claude API."""
    avvik = kontrakt_a.get("avvik", [])
    stats = kontrakt_a.get("sanntidsdata", {}).get("forsinkelsesstatistikk", [])
    bildata = kontrakt_a.get("bildata")
    laert = kontrakt_a.get("bruker", {}).get("preferanser", {}).get("laert", [])

    avvik_tekst = "\n".join(
        f"- {a.get('beskrivelse', '')} (alvorlegheit: {a.get('alvorlighet', 'ukjent')})"
        for a in avvik
    )

    stats_tekst = "\n".join(
        f"- {s.get('linje')} kl {s.get('time_paa_doegnet')}:00: "
        f"median {s.get('median_forsinkelse_min', 0):.0f} min, "
        f"p90 {s.get('p90_forsinkelse_min', 0):.0f} min"
        for s in stats
    )

    bil_tekst = ""
    if bildata:
        bil_tekst = (
            f"Bil via E18: ca. {bildata.get('estimert_reisetid_min', '?')} min "
            f"({bildata.get('avstand_km', '?')} km)"
        )

    laert_tekst = "\n".join(
        f"- Ved {p.get('situasjon', '?')}: vel '{p.get('valgt_handling', '?')}' "
        f"({p.get('antall_ganger', 0)} gonger)"
        for p in laert
    )

    # Bygg alternativ-info med status, togavgang og ankomsttid
    anbefaling_alt_id = anbefaling.get("alternativ_id")
    tog_avgang_tekst = ""
    anbefaling_status = ""
    for alt in kontrakt_a.get("reisealternativer", []):
        if alt.get("id") == anbefaling_alt_id:
            tog_avgang_tekst = _finn_tog_avgang(alt)
            anbefaling_status = alt.get("status", "ukjent")
            break

    andre_med_togavgang = []
    for a in andre:
        a_alt_id = a.get("alternativ_id")
        a_tog_tid = ""
        a_status = ""
        for alt in kontrakt_a.get("reisealternativer", []):
            if alt.get("id") == a_alt_id:
                a_tog_tid = _finn_tog_avgang(alt)
                a_status = alt.get("status", "ukjent")
                break
        ankomst = a.get("estimert_ankomst_hjem", "?")
        ankomst_kort = ankomst[-14:-9] if isinstance(ankomst, str) and len(ankomst) > 14 else (ankomst or "ukjent")
        status_tekst = f", STATUS: {a_status}" if a_status else ""
        andre_med_togavgang.append(
            f"- {a.get('beskrivelse', '')} (tog kl {a_tog_tid or '?'}, heime ca. {ankomst_kort}{status_tekst})"
        )

    andre_tekst = "\n".join(andre_med_togavgang)

    # Samle status for alle alternativ slik at Claude forstaar heilbiletet
    alle_statuser = []
    for alt in kontrakt_a.get("reisealternativer", []):
        linje = ""
        for s in alt.get("steg", []):
            if s.get("linje"):
                linje = s["linje"]
                break
        alle_statuser.append(f"- {linje or 'ukjent'} (alt {alt.get('id')}): {alt.get('status', 'ukjent')}")
    status_oversikt = "\n".join(alle_statuser)

    # Innstillingar
    innstillingar = kontrakt_a.get("sanntidsdata", {}).get("innstillinger", [])
    innst_tekst = "\n".join(
        f"- {i.get('linje', '?')}: {i.get('type', 'ukjent')}"
        for i in innstillingar
    ) if innstillingar else "Ingen innstillingar."

    prompt = f"""Du er ein reiseassistent for ein dagpendlar mellom Drammen og Oslo.
Skriv kort og tydeleg paa norsk. Bruk aa/oe/ae i staden for æøå.

AVVIK:
{avvik_tekst or 'Ingen spesifikke avviksmeldingar, men forsinkingar/innstillingar er oppdaga.'}

STATUS PAA ALLE TOGALTERNATIV:
{status_oversikt}

INNSTILLINGAR:
{innst_tekst}

FORSINKELSESSTATISTIKK (siste 2 timar):
{stats_tekst or 'Ingen data.'}

BILALTERNATIV:
{bil_tekst or 'Ikkje tilgjengeleg.'}

ROLFS PREFERANSAR:
{laert_tekst or 'Ingen laerte preferansar enno.'}

ANBEFALT ALTERNATIV:
- {anbefaling.get('beskrivelse', '')} (tog kl {tog_avgang_tekst or '?'}, heime ca. {str(anbefaling.get('estimert_ankomst_hjem', '?'))[-14:-9] if anbefaling.get('estimert_ankomst_hjem') else '?'}, STATUS: {anbefaling_status or 'ukjent'})

ANDRE ALTERNATIV:
{andre_tekst or 'Ingen.'}

VIKTIG:
- Viss eit tog er FORSINKET eller INNSTILT, maa teksten reflektere dette.
- Ikkje sei at toga "gaar som planlagt" viss status er forsinket/innstilt.
- Viss anbefalinga er forseinka, sei kor mykje forseinka og ny estimert ankomsttid.
- Viss toget er innstilt, sei det tydeleg og foreslaa alternativ.

Skriv to ting, skilt med |||:
1. Ein oppsummering av situasjonen (1-2 setningar, maks 50 ord)
2. Ein kort anbefaling til Rolf (1 setning, maks 30 ord)

Format: oppsummering ||| anbefaling"""

    client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    tekst = response.content[0].text.strip()

    if "|||" in tekst:
        delar = tekst.split("|||", 1)
        oppsummering = delar[0].strip()
        beskrivelse = delar[1].strip()
    else:
        oppsummering = tekst
        beskrivelse = anbefaling.get("beskrivelse", "")

    return oppsummering, beskrivelse
