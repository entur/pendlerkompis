# Spor 2: Motor (all backend-kode)

Du jobber med motoren for Pendlerkompis — all backend-kode lever her.

## Ditt ansvar

1. **Hente data** fra Entur API-er basert paa spesifikasjonene fra Spor 1 (/data)
2. **Forvalte brukerprofiler** (hjem, jobb, avreisetider, laerte preferanser)
3. **Vurdere relevans:** Paavirker avviket brukerens reise?
4. **Tolke situasjonen:** Bruk Claude API til aa generere en forstaelig oppsummering
5. **Finne og rangere alternativer** fra JourneyPlanner
6. **Anbefale:** Velg en tydelig anbefaling + andre alternativer med estimert ankomsttid
7. **Reisevaermelding:** Periodisk vurdering foer avgang, ogsaa naar det ikke er avvik
8. **Eksponere API** som Spor 3 (Presentasjon) konsumerer

## Kontrakt A (intern datamodell)

Se /shared/kontrakt-a.json — dette er dataformatet spesifisert av Spor 1.
Du implementerer koden som henter og strukturerer data i dette formatet.

## Kontrakt B (din output til Spor 3)

Se /shared/kontrakt-b.json — dette leverer du til Presentasjon.
Inneholder: situasjonsoppsummering, anbefaling, andre alternativer.

En anbefaling har ALLTID:
1. Hva som har skjedd (kort, forstaelig for en pendler)
2. En tydelig anbefaling (beste alternativ)
3. Andre alternativer med estimert ankomsttid hjem

## KI-bruk

- Bruk Claude API til aa generere menneskelesbare oppsummeringer og anbefalinger
- Input til LLM: avviksdata + brukerprofil + tilgjengelige alternativer
- Output fra LLM: naturlig spraak-beskrivelse + strukturert anbefaling

## Avgrensning

- Sjekk /data for API-dokumentasjon og spesifikasjoner fra Spor 1
- Du viser IKKE noe til brukeren — det gjoer Spor 3 (Presentasjon)
