# API-strategi for Pendlerkompis

## Kontekst

Rolf har en **kjent pendlerrute** (Drammen ↔ Rådhusgate 5, Oslo). Vi henter reisealternativer, avviksmeldinger, sanntidsdata og historiske forsinkelser for å gi motoren et komplett bilde av dagens trafikksituasjon.

## Valgte API-er

### 1. Journey Planner v3 — Primærkilde (reiser + avvik + sanntid)

**Formål:** Hente reisealternativer, avviksmeldinger og sanntidsestimater i **ett kall**. Journey Planner integrerer allerede SIRI SX (situasjonsmeldinger) og SIRI ET (sanntidsestimater) i responsene sine — vi slipper å kalle disse separat.

**Endepunkt:**
```
POST https://api.entur.io/journey-planner/v3/graphql
```

**GraphQL-spørring:** `trip`-query med `from`/`to`-koordinater og `dateTime`.

**Data vi henter per reisealternativ:**
- `aimedDepartureTime` / `expectedDepartureTime` — planlagt vs. estimert avgang ved origin
- `aimedArrivalTime` / `expectedArrivalTime` — planlagt vs. estimert ankomst ved destinasjon
- `cancellation` — innstilling på stopp-nivå og journeynivå
- `situations` — avviksmeldinger (SIRI SX) knyttet til hvert reiseben
- `serviceJourney.id` — brukes til oppslag mot invalid-ET API
- `line.publicCode` / `line.transportMode` — linjenummer og transportmiddel

**Tre kall gjøres:**

| Kall | Formål | Parametre |
|------|--------|-----------|
| Nåværende reiser | Rolfs reisealternativer | `dateTime` = brukerens avreisetid, 5 trip patterns |
| Historiske reiser (2t tilbake) | Empiriske forsinkelser for samme rute | `dateTime` = avreisetid − 2 timer, 10 trip patterns |
| Quay-avganger ved destinasjon | Bredere bilde av kanselleringer/forsinkelser | `quay(id)` + `estimatedCalls(numberOfDepartures: 20)` |

**Autentisering:** Header `ET-Client-Name: entur-pendlerkompis`

---

### 2. Realtime invalid-ET — Historiske ankomster (fallback)

**Formål:** Hente faktiske ankomsttider for nylige avganger på Rolfs linjer.

**Endepunkt:**
```
POST https://api.entur.io/realtime/invalid-et/graphql
```

**Viktige egenskaper:**
- Spørres med `serviceJourneyId`-er hentet fra de historiske trip-spørringene
- Gir `actualArrivalTime` (faktisk ankomst), ikke bare `expectedArrivalTime`
- Brukes til å beregne empiriske forsinkelser (median og 90-persentil)

**Fallback:** Dersom endepunktet ikke er tilgjengelig, beregner vi forsinkelser fra de historiske Journey Planner-responsene (`expectedArrivalTime` − `aimedArrivalTime`). Dette gir noe lavere presisjon (estimert vs. faktisk), men er tilstrekkelig.

---

## API-er vi IKKE bruker (og hvorfor)

| API | Grunn til å utelate |
|---|---|
| **SIRI SX (REST)** | Journey Planner inkluderer situasjonsmeldinger via `situations`-feltet — separat kall er unødvendig |
| **SIRI ET (REST)** | Journey Planner inkluderer sanntidsestimater via `expectedDepartureTime`/`expectedArrivalTime` |
| **GTFS-RT Service Alerts** | Duplikat av SIRI SX i protobuf-format |
| **GTFS-RT Trip Updates** | Duplikat av SIRI ET |
| **SIRI VM (Vehicle Monitoring)** | GPS-posisjonsdata — ikke relevant for avviksvarsling |

---

## Dataflyt

```
┌──────────────────────────────────────────────────────┐
│  Journey Planner v3 (3 parallelle kall)              │
│                                                      │
│  1. trip(nå)         → Reisealternativer + avvik     │
│  2. trip(−2 timer)   → Historiske serviceJourneyIds  │
│  3. quay(destinasjon)→ Live kanselleringer           │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│  invalid-ET (valgfritt)                              │
│  → Faktiske ankomsttider for historiske avganger     │
│  → Fallback: beregn fra historiske trip-responser    │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│  Transform + beregning                               │
│                                                      │
│  → avvik[] fra situations (SIRI SX)                  │
│  → reisealternativer[] med status og steg            │
│  → sanntidsdata:                                     │
│      faktiske_ankomster (siste 2 timer)              │
│      forsinkelsesstatistikk (median/p90 per linje)   │
│      innstillinger (kanselleringer)                  │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
          Bygg Kontrakt A (utvidet)
          (bruker + avvik + alternativer + sanntidsdata)
                   │
                   ▼
          Motor analyserer → Kontrakt B
```

## Kontrakt A — utvidet med sanntidsdata

I tillegg til standard Kontrakt A (`bruker`, `avvik`, `reisealternativer`) leverer vi en `sanntidsdata`-seksjon:

```json
{
  "sanntidsdata": {
    "faktiske_ankomster": [
      {
        "service_journey_id": "VYG:ServiceJourney:821_444401-R",
        "linje": "RE11",
        "planlagt_ankomst": "2026-03-25T15:12:00+01:00",
        "faktisk_ankomst": "2026-03-25T15:15:00+01:00",
        "forsinkelse_min": 3.0,
        "innstilt": false
      }
    ],
    "forsinkelsesstatistikk": [
      {
        "linje": "RE11",
        "stasjon": "Drammen",
        "time_paa_doegnet": 16,
        "median_forsinkelse_min": 2.0,
        "p90_forsinkelse_min": 8.5,
        "antall_observasjoner": 4
      }
    ],
    "innstillinger": [
      {
        "service_journey_id": "VYG:ServiceJourney:823_444403-R",
        "linje": "RE11",
        "type": "hel_tur",
        "paavirket_stasjon": null
      }
    ]
  }
}
```

Denne seksjonen er additiv — den bryter ikke Kontrakt A for konsumenter som ignorerer den.

## Bruk (CLI)

```bash
cd pendlerkompis
PYTHONPATH=. .venv/bin/python -m data.main --direction fra_jobb
PYTHONPATH=. .venv/bin/python -m data.main --direction fra_hjem --time 07:15
```

## Autentisering

Alle Entur API-er er åpne under NLOD-lisens. Ingen API-nøkkel kreves, men alle kall **må** inkludere headeren:

```
ET-Client-Name: entur-pendlerkompis
```

Manglende header kan føre til rate-limiting eller blokkering.
