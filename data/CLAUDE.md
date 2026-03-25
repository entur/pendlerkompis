# Spor 1: Data (spesifikasjon)

Du jobber med dataspesifikasjon for Pendlerkompis. Dette er et spesifikasjonsspor — du skriver IKKE applikasjonskode.

## Ditt ansvar

1. **Utforske Entur API-er** — finn ut hvilke endepunkter som finnes, hva de returnerer, og hvordan de kalles
2. **Spesifisere dataformat** — definer Kontrakt A (hva Motor trenger)
3. **Dokumentere API-kall** — skriv eksempler paa hvordan data hentes (URL, parametere, respons)
4. **Lage mock-data** — realistiske eksempler i /shared som Motor og Presentasjon kan jobbe mot
5. **Spesifisere brukerprofil** — hva som lagres om Rolf og hans preferanser

## Leveranser

- Dokumentasjon av Entur API-er (SIRI-SX, SIRI-ET, JourneyPlanner)
- Kontrakt A (JSON-skjema) i /shared/kontrakt-a.json
- Mock-data i /shared
- API-kall-eksempler som Spor 2 kan implementere

## Entur API-er aa utforske

- **SIRI-SX:** Situasjonsmeldinger (avvik, innstillinger) — developer.entur.org
- **SIRI-ET:** Estimert sanntid for avganger
- **JourneyPlanner (OTP):** Rutesoek, alternative reiser

## Avgrensning

- Du skriver IKKE applikasjonskode — det gjoer Spor 2 (Motor)
- Du implementerer IKKE datahenting — du spesifiserer hvordan det skal gjoeres
- Du leverer dokumentasjon og spesifikasjoner som Spor 2 koder mot
