# Pendlerkompis

KI-drevet reiseassistent som proaktivt varsler dagpendlere om avvik og gir personlige anbefalinger.

## Arkitektur

Tre spor i en pipeline:

```
┌──────────────┐  Kontrakt A  ┌──────────────┐  Kontrakt B  ┌──────────────┐
│  Spor 1:     │─────────────>│  Spor 2:     │─────────────>│  Spor 3:     │
│  DATA INN    │              │  MOTOR       │              │  PRESENTASJON│
│  /data       │              │  /motor      │              │  /presentasjon│
└──────────────┘              └──────────────┘              └──────────────┘
```

- **Spor 1 (Data inn):** Henter avviksdata fra Entur API-er og forvalter brukerprofiler
- **Spor 2 (Motor):** Analyserer data, bruker Claude API til aa tolke situasjonen, og genererer anbefalinger
- **Spor 3 (Presentasjon):** Frontend/UI som viser varsler, vaermelding og onboarding til brukeren

## Mappestruktur

```
/data            # Spor 1: Datahenting (Entur API) og brukerprofil
/motor           # Spor 2: Analyse og KI (Claude API)
/presentasjon    # Spor 3: Frontend/UI
/shared          # Kontrakter (A + B) og mock-data
```

Hver mappe har sin egen CLAUDE.md med sporspesifikk kontekst.

## Persona: Erfarne Rolf

Dagpendler Drammen <-> Raadhusgata 5, Oslo. Kjenner reisen sin godt.

## Brukerreise (fire steg)

1. **Oppstart:** Rolf oppgir hjem, jobb og avreisetider
2. **Avvik:** Notifikasjon med en tydelig anbefaling + alternativer med estimert ankomsttid
3. **Laering:** Fange opp Rolfs valg for aa forbedre fremtidige anbefalinger
4. **Reisevaermelding:** Periodisk status foer avgang, uansett om det er avvik eller ikke

## Kontrakt A: Data -> Motor

Se /shared/kontrakt-a.json for skjema.

Spor 1 leverer strukturert data til Spor 2:

```json
{
  "bruker": {
    "id": "rolf-1",
    "hjem": { "navn": "Drammen", "koordinater": { "lat": 59.7441, "lon": 10.2045 } },
    "jobb": { "navn": "Raadhusgata 5, Oslo", "koordinater": { "lat": 59.9118, "lon": 10.7340 } },
    "avreisetider": {
      "fra_hjem": "07:15",
      "fra_jobb": "16:30"
    },
    "preferanser": {
      "laert": []
    }
  },
  "avvik": [
    {
      "id": "sx-12345",
      "kilde": "SIRI-SX",
      "type": "signalfeil",
      "alvorlighet": "hoy",
      "beskrivelse": "Signalfeil ved Asker stasjon",
      "paavirker_linjer": ["L1", "RE11"],
      "paavirker_stasjoner": ["Asker"],
      "estimert_varighet_min": 60,
      "oppstaat": "2026-03-25T14:30:00+01:00"
    }
  ],
  "reisealternativer": [
    {
      "id": "alt-1",
      "beskrivelse": "Tog fra Oslo S kl 15:02",
      "avgang": "2026-03-25T15:02:00+01:00",
      "estimert_ankomst": "2026-03-25T16:15:00+01:00",
      "steg": [
        { "type": "gange", "fra": "Raadhusgata 5", "til": "Oslo S", "varighet_min": 12 },
        { "type": "tog", "linje": "RE11", "fra": "Oslo S", "til": "Drammen", "varighet_min": 50 }
      ],
      "status": "i_rute"
    },
    {
      "id": "alt-2",
      "beskrivelse": "Buss 31 til Lysaker, tog videre",
      "avgang": "2026-03-25T16:35:00+01:00",
      "estimert_ankomst": "2026-03-25T18:00:00+01:00",
      "steg": [
        { "type": "gange", "fra": "Raadhusgata 5", "til": "Jernbanetorget", "varighet_min": 8 },
        { "type": "buss", "linje": "31", "fra": "Jernbanetorget", "til": "Lysaker", "varighet_min": 25 },
        { "type": "tog", "linje": "L1", "fra": "Lysaker", "til": "Drammen", "varighet_min": 40 }
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
    "oppsummering": "Signalfeil ved Asker paavirker hjemreisen din. Toget kl 16:42 er trolig innstilt.",
    "alvorlighet": "hoy",
    "avvik_ids": ["sx-12345"]
  },
  "anbefaling": {
    "handling": "reis_tidligere",
    "beskrivelse": "Gaa fra jobb naa. Ta 15:02-toget fra Oslo S.",
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
      "beskrivelse": "Vent -- feilen forventes loest innen kl 16. Reis som normalt.",
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

For reisevaermelding brukes samme format men med `"type": "vaermelding"` og lavere alvorlighet.

## Regler

- Hvert spor jobber i sin egen mappe og paa sin egen branch
- /shared endres kun etter avtale i teamet
- Mock-data i /shared brukes til alle spor kan integreres
- En notifikasjon har alltid: (1) hva som skjedde, (2) en tydelig anbefaling, (3) andre alternativer med ankomsttid
