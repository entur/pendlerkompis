# API-strategi for Pendlerkompis

## Kontekst

Rolf har en **kjent pendlerrute** (Drammen ↔ Rådhusgate 5, Oslo). Vi trenger ikke planlegge ruten hans på nytt hver dag — vi trenger å **overvåke den** og reagere på avvik.

## Valgte API-er

### 1. SIRI SX — Situation Exchange (avviksmeldinger)

**Formål:** Oppdage avvik som påvirker Rolfs rute (signalfeil, innstillinger, stenginger).

**Endepunkt (REST/SIRI Lite):**
```
GET https://api.entur.io/realtime/v1/rest/sx?requestorId=<UUID>
```

**Viktige egenskaper:**
- Bruk fast `requestorId` (UUID) for å kun hente endringer siden sist
- Returnerer tekstmeldinger knyttet til linjer, stasjoner og avganger
- Dekker alle operatører: Vy (NSB/VYG), Go-Ahead (GOA), Brakar (BRA), Flytoget (FLT) m.fl.
- Filtrér på Rolfs linjer (L1, RE11) og stasjoner (Drammen, Asker, Oslo S)

**Når:** Polles jevnlig (~60 sekunder) for å fange opp nye avvik.

**Datakilde i Kontrakt A:** `"kilde": "SIRI-SX"`

---

### 2. SIRI ET — Estimated Timetable (sanntidsestimater)

**Formål:** Oppdage forsinkelser på Rolfs konkrete avganger, selv uten en SX-melding.

**Endepunkt (REST/SIRI Lite):**
```
GET https://api.entur.io/realtime/v1/rest/et?requestorId=<UUID>
```

**Viktige egenskaper:**
- Gir planlagt vs. estimert avgangs-/ankomsttid per avgang
- Inkluderer kanselleringer og endringer i stoppmønster
- Bruk fast `requestorId` for inkrementelle oppdateringer
- Filtrer på Rolfs avgangstider og linjer

**Når:** Polles jevnlig (~60 sekunder), spesielt rundt Rolfs avreisetider (07:15, 16:30).

**Datakilde i Kontrakt A:** `"kilde": "SIRI-ET"`

---

### 3. Journey Planner v3 — Reiseplanlegger (alternativer)

**Formål:** Finne alternative reiser **kun når avvik er oppdaget**.

**Endepunkt:**
```
POST https://api.entur.io/journey-planner/v3/graphql
```

**Viktige egenskaper:**
- GraphQL API med sanntid og avviksinformasjon innebygd
- Returnerer komplette reisealternativer med estimert ankomst
- Inkluderer `situations`-felt på hvert reiseben (avviksmeldinger)
- Støtter filtrering på transportmiddel, operatør og tidsrom

**Når:** On-demand — trigges kun når SIRI SX eller ET avdekker et problem.

**Autentisering:** Header `ET-Client-Name: pendlerkompis-motor`

---

## API-er vi IKKE bruker

| API | Grunn til å utelate |
|---|---|
| **GTFS-RT Service Alerts** | Duplikat av SIRI SX, bare i protobuf-format |
| **GTFS-RT Trip Updates** | Duplikat av SIRI ET |
| **SIRI VM (Vehicle Monitoring)** | Posisjonsdata — ikke relevant for avviksvarsling |
| **Journey Planner for normalrute** | Rolf kjenner ruten sin, trenger ikke planlegge den daglig |

---

## Dataflyt

```
┌──────────────────────────────────────────────┐
│  Polling (~60s)                              │
│                                              │
│  SIRI SX  → Avvik på Rolfs linjer/stasjon?  │
│  SIRI ET  → Forsinkelse på hans avganger?    │
└──────────────────┬───────────────────────────┘
                   │
                   │ Avvik oppdaget
                   ▼
┌──────────────────────────────────────────────┐
│  Journey Planner v3 (on-demand)              │
│  → Hent alternative reiser fra nåværende     │
│    posisjon til destinasjon                  │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
          Bygg Kontrakt A-objekt
          (bruker + avvik + alternativer)
                   │
                   ▼
          Motor analyserer → Kontrakt B
          (anbefaling til bruker)
```

## Reiseværmelding (uten avvik)

Også ved **normalsituasjon** (ingen avvik) skal Rolf få en periodisk statusmelding før avgang. Da brukes:

- **SIRI ET** — bekreft at avgangen er i rute
- **Journey Planner v3** — eventuelt for å bekrefte normalt reisetidsestimat

Kontrakt B sendes med `"type": "vaermelding"` og lav alvorlighet.

## Autentisering

Alle Entur API-er er åpne under NLOD-lisens. Ingen API-nøkkel kreves, men alle kall **må** inkludere headeren:

```
ET-Client-Name: pendlerkompis-motor
```

Manglende header kan føre til rate-limiting eller blokkering.
