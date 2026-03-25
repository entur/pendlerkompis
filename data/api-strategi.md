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

### 3. OSRM — Fri-flyt reisetid for bil

**Formål:** Hente baseline kjørerute og reisetid uten trafikk.

**Endepunkt:**
```
GET http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false
```

**Data vi henter:**
- `distance` — kjøreavstand i meter
- `duration` — fri-flyt reisetid i sekunder

**Autentisering:** Ingen. Offentlig demo-server.

---

### 4. Vegvesen Trafikkdata — Trafikkvolum som kø-indikator

**Formål:** Hente sanntids trafikkvolum fra tellepunkter langs E18 for å estimere kø-nivå.

**Endepunkt:**
```
POST https://trafikkdata-api.atlas.vegvesen.no/ (GraphQL)
```

**Data vi henter:**
- Kjøretøyvolum per time ved 5 representative E18-stasjoner (Bangeløkka, Tranby, Maritim, Frognerstranda, Bangeløkka nord)
- Historisk gjennomsnitt for samme time/ukedag (siste 4 uker)

**Beregning:** `kapasitetsutnyttelse = volum_nå / volum_normalt`. Brukes til å justere fri-flyt reisetiden: `estimert_reisetid = fri_flyt * snitt(kapasitetsutnyttelse)`, maks 2.5x.

**Autentisering:** Ingen. Åpent GraphQL-API.

**Begrensninger:** Gir volum, ikke hastighet. Trafikkvolum er en indirekte kø-indikator — høyt volum betyr ikke nødvendigvis kø, men korrelerer godt i rushtid.

---

### 5. MET.no Locationforecast 2.0 — Værdata

**Formål:** Hente værprognose for avgangsstedet ved avreisetidspunkt. Gir motoren kontekst om temperatur, vind og nedbør som kan påvirke reisevalg og anbefalinger.

**Endepunkt:**
```
GET https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}
```

**Data vi henter:**
- `air_temperature` — lufttemperatur i °C
- `wind_speed` — vindstyrke i m/s
- `precipitation_amount` — nedbør neste time i mm (fra `next_1_hours`)
- `symbol_code` — Yr-symbolkode (f.eks. `cloudy`, `rain`, `clearsky_day`)

**Logikk:** Vi henter hele tidsserien og velger oppføringen nærmest brukerens avreisetidspunkt.

**Autentisering:** Ingen API-nøkkel, men `User-Agent`-header er **påkrevd** per MET.no sine bruksvilkår.

**Begrensninger:** Prognose-presisjon avhenger av hvor langt frem i tid avgangen er. Inntil ~48 timer frem er oppløsningen per time.

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
    ┌──────────────┼──────────────────┐
    ▼              ▼                  ▼
┌────────────┐ ┌───────────────┐ ┌──────────────────┐
│ invalid-ET │ │ OSRM (bil)    │ │ Vegvesen         │
│ (valgfri)  │ │ → fri-flyt    │ │ Trafikkdata      │
│ → faktiske │ │   reisetid    │ │ → volum nå       │
│   ankomst  │ │   + avstand   │ │ → volum historisk │
└──────┬─────┘ └──────┬────────┘ └────────┬─────────┘
       │              │                    │
       │         ┌────┴────┐               │
       │         │ MET.no  │               │
       │         │ → vær-  │               │
       │         │ prognose│               │
       │         └────┬────┘               │
       ▼              ▼                    ▼
┌──────────────────────────────────────────────────────┐
│  Transform + beregning                               │
│                                                      │
│  → avvik[] fra situations (SIRI SX)                  │
│  → reisealternativer[] med status og steg            │
│  → sanntidsdata (forsinkelser, kanselleringer)        │
│  → bildata (fri-flyt + trafikkjustert reisetid)      │
│  → vaerdata (temperatur, vind, nedbør)                │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
      Bygg Kontrakt A (utvidet)
      (bruker + avvik + alternativer + sanntidsdata + bildata + vaerdata)
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

### bildata — bil-alternativ

```json
{
  "bildata": {
    "reisetid_fri_flyt_min": 39.0,
    "avstand_km": 41.9,
    "trafikk_punkter": [
      {
        "stasjon": "E18 Bangeløkka Sydgående",
        "volum_siste_time": 672,
        "volum_normalt": 580,
        "kapasitetsutnyttelse": 1.16
      }
    ],
    "estimert_reisetid_min": 45,
    "kilde": "osrm+vegvesen_trafikkdata"
  }
}
```

### vaerdata — værprognose ved avgang

```json
{
  "vaerdata": {
    "tidspunkt": "2026-03-25T16:00:00Z",
    "lufttemperatur_c": 4.2,
    "vindstyrke_ms": 3.8,
    "nedbor_neste_time_mm": 0.3,
    "symbolkode": "cloudy",
    "kilde": "met.no/locationforecast/2.0"
  }
}
```

Alle tilleggsseksjoner er additive — de bryter ikke Kontrakt A for konsumenter som ignorerer dem.

## Bruk (CLI)

```bash
cd pendlerkompis
PYTHONPATH=. .venv/bin/python -m data.main --direction fra_jobb
PYTHONPATH=. .venv/bin/python -m data.main --direction fra_hjem --time 07:15
```

## Autentisering

**Entur API-er:** Åpne under NLOD-lisens. Ingen API-nøkkel, men alle kall **må** inkludere headeren `ET-Client-Name: entur-pendlerkompis`.

**OSRM:** Offentlig demo-server, ingen autentisering.

**Vegvesen Trafikkdata:** Åpent GraphQL-API, ingen autentisering.

**MET.no Locationforecast:** Åpent API under norsk lisens. Ingen API-nøkkel, men `User-Agent`-header med appnavn og kontakt er **påkrevd**.
