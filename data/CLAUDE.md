# Spor 1: Data inn

Du jobber med datahenting og brukerprofil for Pendlerkompis.

## Ditt ansvar

1. **Hente avviksdata** fra Entur sine API-er (SIRI-SX, sanntid)
2. **Hente reisealternativer** fra JourneyPlanner/OTP
3. **Forvalte brukerprofiler** (hjem, jobb, avreisetider, laerte preferanser)
4. **Levere strukturert data** til Spor 2 (Motor) via Kontrakt A

## Kontrakt A (din output)

Se /shared/kontrakt-a.json for eksakt skjema og CLAUDE.md i rot for eksempel.

Du leverer et JSON-objekt med:
- `bruker` — profil med hjem, jobb, avreisetider, preferanser
- `avvik` — aktive avvik fra SIRI-SX som paavirker brukerens rute
- `reisealternativer` — tilgjengelige reiseruter fra JourneyPlanner

## Entur API-er

- **SIRI-SX:** Situasjonsmeldinger (avvik, innstillinger) — developer.entur.org
- **SIRI-ET:** Estimert sanntid for avganger
- **JourneyPlanner (OTP):** Rutesoek, alternative reiser

## Avgrensning

- Du tolker IKKE avvikene — det gjoer Spor 2 (Motor)
- Du presenterer IKKE noe til brukeren — det gjoer Spor 3 (Presentasjon)
- Du leverer raadata og alternativer, strukturert etter Kontrakt A
