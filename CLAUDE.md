# Pendlerkompis

KI-drevet reiseassistent som proaktivt varsler dagpendlere om avvik og gir personlige anbefalinger.

## Arkitektur

Tre spor i en pipeline. Spor 1 er et spesifikasjonsspor — all kode lever i Spor 2 og 3.

```
┌──────────────┐  Kontrakt A  ┌──────────────┐  Kontrakt B  ┌──────────────┐
│  Spor 1:     │  (spek/dok)  │  Spor 2:     │─────────────>│  Spor 3:     │
│  DATA        │─────────────>│  MOTOR       │              │  PRESENTASJON│
│  (spesifik.) │              │  (all kode)  │              │  (frontend)  │
│  /data       │              │  /motor      │              │  /presentasjon│
└──────────────┘              └──────────────┘              └──────────────┘
```

- **Spor 1 (Data):** Utforsker Entur API-er, spesifiserer dataformat, dokumenterer brukerprofil. Leverer Kontrakt A og API-dokumentasjon. **Skriver ikke applikasjonskode.**
- **Spor 2 (Motor):** All backend-kode. Henter data fra Entur API-er (basert på Spor 1 sin spesifikasjon), analyserer, bruker Claude API, genererer anbefalinger. Leverer Kontrakt B.
- **Spor 3 (Presentasjon):** Frontend/UI. Konsumerer Kontrakt B, viser varsler og værmelding.

## Mappestruktur

```
/docs              # Tverrfaglig ledelse — kontekst og spesifikasjoner
  /produkt         #   Produktleder — persona, verdiforslag, viability
  /design          #   Designer — brukerreiser, brukerinnsikt, interaksjonsmønster
  /team            #   Teamlead — way of work, prosess, seremonier
/data              # Spor 1 (teknologi) — API-dokumentasjon, dataformat-spesifikasjon
/motor             # Spor 2 (teknologi) — all backend-kode
/presentasjon      # Spor 3 (teknologi) — frontend/UI-kode
/shared            # Kontrakter (A + B) og mock-data
```

Hver mappe har sin egen CLAUDE.md med kontekst for den som jobber der.

## Tverrfaglig ledelse — fire dimensjoner

Enturs modell med fire ledelsesdimensjoner reflekteres i /docs:

| Dimensjon | Ansvar | Mappe | Skriver |
|-----------|--------|-------|---------|
| **Produkt** | Persona, verdiforslag, viability, leveranseansvar | /docs/produkt | Produktleder |
| **Design** | Brukerreiser, brukerinnsikt, interaksjonsmønster, DesignOps | /docs/design | Designer |
| **Team** | Way of work, prosess, seremonier, metoder | /docs/team | Teamlead |
| **Teknologi** | Arkitektur, teknologivalg, feasibility | /data, /motor, /presentasjon, /shared | Utviklere |

## Fileierskap — hvordan unngå konflikter

Konflikter unngås ved at hver dimensjon eier sine mapper. Alle kan *lese* alt, men kun eier *skriver*.

- Produktleder skriver i /docs/produkt — utviklere og designer *leser* for kontekst
- Designer skriver i /docs/design — Spor 3 (presentasjon) *leser* for UI-retning
- Teamlead skriver i /docs/team — alle *leser* for prosess og arbeidsflyt
- Utviklere skriver i /data, /motor, /presentasjon — eid av sine respektive spor
- /shared (kontrakter) endres kun etter tverrfaglig avtale
- CLAUDE.md (rot) eies av teamlead — den felles konteksten for alle Claude Code-sesjoner

**Regel:** Hvis du trenger å endre en fil du ikke eier, avtal med eier først.

## Persona: Rutinerte Rolf

Dagpendler Drammen <-> Rådhusgata 5, Oslo. Kjenner reisen sin godt.

## Brukerreise (fire steg)

1. **Oppstart:** Rolf oppgir hjem, jobb og avreisetider
2. **Avvik:** Notifikasjon med én tydelig anbefaling + alternativer med estimert ankomsttid
3. **Læring:** Fange opp Rolfs valg for å forbedre fremtidige anbefalinger
4. **Reiseværmelding:** Periodisk status før avgang, uansett om det er avvik eller ikke

## Kontrakt A: Data -> Motor

Se /shared/kontrakt-a.json for skjema.

Spor 1 spesifiserer dataformatet. Spor 2 implementerer hentingen.

```json
{
  "bruker": {
    "id": "rolf-1",
    "hjem": { "navn": "Drammen", "koordinater": { "lat": 59.7441, "lon": 10.2045 } },
    "jobb": { "navn": "Rådhusgata 5, Oslo", "koordinater": { "lat": 59.9118, "lon": 10.7340 } },
    "avreisetider": {
      "fra_hjem": "07:15",
      "fra_jobb": "16:30"
    },
    "preferanser": {
      "lært": []
    }
  },
  "avvik": [
    {
      "id": "sx-12345",
      "kilde": "SIRI-SX",
      "type": "signalfeil",
      "alvorlighet": "høy",
      "beskrivelse": "Signalfeil ved Asker stasjon",
      "påvirker_linjer": ["L1", "RE11"],
      "påvirker_stasjoner": ["Asker"],
      "estimert_varighet_min": 60,
      "oppstått": "2026-03-25T14:30:00+01:00"
    }
  ],
  "reisealternativer": [
    {
      "id": "alt-1",
      "beskrivelse": "Tog fra Oslo S kl 15:02",
      "avgang": "2026-03-25T15:02:00+01:00",
      "estimert_ankomst": "2026-03-25T16:15:00+01:00",
      "steg": [
        { "type": "gange", "fra": "Rådhusgata 5", "til": "Oslo S", "varighet_min": 12 },
        { "type": "tog", "linje": "RE11", "fra": "Oslo S", "til": "Drammen", "varighet_min": 50 }
      ],
      "status": "i_rute"
    }
  ]
}
```

## Kontrakt B: Motor -> Presentasjon

Se /shared/kontrakt-b.json for skjema.

Spor 2 leverer ferdig tolket anbefaling til Spor 3:

```json
{
  "bruker_id": "rolf-1",
  "type": "avvik",
  "tidspunkt": "2026-03-25T14:45:00+01:00",
  "situasjon": {
    "oppsummering": "Signalfeil ved Asker påvirker hjemreisen din. Toget kl 16:42 er trolig innstilt.",
    "alvorlighet": "høy",
    "avvik_ids": ["sx-12345"]
  },
  "anbefaling": {
    "handling": "reis_tidligere",
    "beskrivelse": "Gå fra jobb nå. Ta 15:02-toget fra Oslo S.",
    "alternativ_id": "alt-1",
    "estimert_ankomst_hjem": "2026-03-25T16:15:00+01:00"
  },
  "andre_alternativer": [
    {
      "handling": "alternativ_rute",
      "beskrivelse": "Buss 31 til Lysaker, tog videre til Drammen",
      "alternativ_id": "alt-2",
      "estimert_ankomst_hjem": "2026-03-25T18:00:00+01:00"
    },
    {
      "handling": "utsett",
      "beskrivelse": "Vent — feilen forventes løst innen kl 16. Reis som normalt.",
      "alternativ_id": null,
      "estimert_ankomst_hjem": "2026-03-25T17:50:00+01:00"
    },
    {
      "handling": "ikke_reis",
      "beskrivelse": "Jobb hjemmefra i dag",
      "alternativ_id": null,
      "estimert_ankomst_hjem": null
    }
  ]
}
```

For reiseværmelding brukes samme format men med `"type": "værmelding"` og lavere alvorlighet.

## Regler

- **Norsk tekst skal alltid bruke æ, ø og å — aldri substitusjonene aa, oe, ae.** Hvis du finner eksisterende tekst med slike substitusjoner, fiks dem.
- Spor 1 skriver spesifikasjoner og dokumentasjon, IKKE applikasjonskode
- All applikasjonskode lever i Spor 2 (motor) og Spor 3 (presentasjon)
- Hvert spor jobber i sin egen mappe og på sin egen branch
- /shared endres kun etter avtale i teamet
- Mock-data i /shared brukes til alle spor kan integreres
- En notifikasjon har alltid: (1) hva som skjedde, (2) en tydelig anbefaling, (3) andre alternativer med ankomsttid
