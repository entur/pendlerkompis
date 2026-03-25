# Spor 2: Motor (analyse og KI)

Du jobber med analysemotoren for Pendlerkompis — hjernen i systemet.

## Ditt ansvar

1. **Vurdere relevans:** Paavirker avviket brukerens reise?
2. **Tolke situasjonen:** Bruk Claude API til aa generere en forstaelig oppsummering
3. **Finne alternativer:** Velg og ranger reisealternativer fra Spor 1
4. **Anbefale:** Velg en tydelig anbefaling + andre alternativer med estimert ankomsttid
5. **Reisevaermelding:** Periodisk vurdering foer avgang, ogsaa naar det ikke er avvik

## Kontrakt A (din input)

Se /shared/kontrakt-a.json — dette faar du fra Spor 1.
Inneholder: brukerprofil, aktive avvik, tilgjengelige reisealternativer.

## Kontrakt B (din output)

Se /shared/kontrakt-b.json — dette leverer du til Spor 3.
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

- Du henter IKKE data selv — det gjoer Spor 1 (Data inn)
- Du viser IKKE noe til brukeren — det gjoer Spor 3 (Presentasjon)
- Du tar inn Kontrakt A og leverer Kontrakt B
