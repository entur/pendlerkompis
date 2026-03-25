"""Builds the prompt sent to Claude for journey analysis."""

from __future__ import annotations

import json


KONTRAKT_B_SCHEMA = """
{
  "bruker_id": "string",
  "type": "avvik" | "vaermelding",
  "tidspunkt": "ISO-8601 datetime",
  "situasjon": {
    "oppsummering": "string — menneskelesbar oppsummering av situasjonen",
    "alvorlighet": "ingen" | "lav" | "middels" | "hoy",
    "avvik_ids": ["string"]
  },
  "anbefaling": {
    "handling": "reis_som_normalt" | "reis_tidligere" | "utsett" | "alternativ_rute" | "ikke_reis",
    "beskrivelse": "string — tydelig beskrivelse av hva Rolf bør gjøre",
    "alternativ_id": "string | null — referanse til reisealternativ fra input",
    "estimert_ankomst_hjem": "ISO-8601 datetime | null"
  },
  "andre_alternativer": [
    {
      "handling": "...",
      "beskrivelse": "string",
      "alternativ_id": "string | null",
      "estimert_ankomst_hjem": "ISO-8601 datetime | null"
    }
  ]
}
"""


def build_prompt(kontrakt_a: dict) -> str:
    bruker = kontrakt_a["bruker"]
    avvik = kontrakt_a.get("avvik", [])
    alternativer = kontrakt_a.get("reisealternativer", [])
    sanntid = kontrakt_a.get("sanntidsdata", {})
    innstillinger = sanntid.get("innstillinger", [])
    statistikk = sanntid.get("forsinkelsesstatistikk", [])
    faktiske = sanntid.get("faktiske_ankomster", [])
    preferanser = bruker.get("preferanser", {}).get("laert", [])

    har_avvik = len(avvik) > 0
    har_innstillinger = len(innstillinger) > 0
    antall_forsinket = sum(
        1 for a in alternativer if a.get("status") in ("forsinket", "innstilt")
    )

    situasjonstype = "avvik" if (har_avvik or har_innstillinger or antall_forsinket > 0) else "vaermelding"

    prompt = f"""Du er en reiseassistent for Pendlerkompis. Analyser reisesituasjonen for pendler Rolf og generer en anbefaling.

## Bruker
- ID: {bruker['id']}
- Rute: {bruker['hjem']['navn']} ↔ {bruker['jobb']['navn']}
- Avreisetider: fra hjem {bruker['avreisetider']['fra_hjem']}, fra jobb {bruker['avreisetider']['fra_jobb']}

## Lærte preferanser (fra tidligere valg)
{json.dumps(preferanser, ensure_ascii=False, indent=2) if preferanser else "Ingen lærte preferanser ennå."}

## Avvik (SIRI-SX situasjonsmeldinger)
{json.dumps(avvik, ensure_ascii=False, indent=2) if avvik else "Ingen aktive avvik."}

## Reisealternativer
{json.dumps(alternativer, ensure_ascii=False, indent=2)}

## Sanntidsdata
### Innstillinger (kanselleringer)
{json.dumps(innstillinger, ensure_ascii=False, indent=2) if innstillinger else "Ingen registrerte innstillinger."}

### Forsinkelsesstatistikk (siste 2 timer)
{json.dumps(statistikk, ensure_ascii=False, indent=2) if statistikk else "Ingen statistikk tilgjengelig."}

### Faktiske ankomster (siste 2 timer)
{json.dumps(faktiske, ensure_ascii=False, indent=2) if faktiske else "Ingen faktiske ankomster registrert."}

## Din oppgave

Basert på dataene ovenfor:

1. Vurder om Rolfs reise er påvirket (se status på alternativer, avvik, innstillinger)
2. Ta hensyn til lærte preferanser (f.eks. foretrekker Rolf å reise tidligere ved signalfeil)
3. Velg én tydelig anbefaling med handling og beskrivelse
4. List opp 2–3 andre alternativer med estimert ankomsttid

Situasjonstype: **{situasjonstype}**

## Svarformat

Svar KUN med et gyldig JSON-objekt (ingen markdown, ingen forklaring utenfor JSON):

{KONTRAKT_B_SCHEMA}

Regler:
- "oppsummering" skal være kortfattet og menneskevennlig (én setning, maks to)
- "beskrivelse" i anbefaling skal si konkret hva Rolf bør gjøre nå (tog/buss/tidspunkt)
- "andre_alternativer" skal ha de andre reisealternativene med realistiske ankomsttider
- Bruk alltid æ, ø og å — aldri aa, oe, ae
- "tidspunkt" settes til nå (ISO-8601 med tidssone +01:00)
"""
    return prompt
