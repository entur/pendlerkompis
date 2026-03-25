# Spor 3: Presentasjon

Du jobber med frontend/UI for Pendlerkompis — det Erfarne Rolf ser og interagerer med.

## Ditt ansvar

1. **Onboarding:** La Rolf oppgi hjem, jobb og avreisetider
2. **Avviksvarsel:** Vise notifikasjon med anbefaling og alternativer
3. **Reisevaermelding:** Vise periodisk status foer avgang
4. **Fange Rolfs valg:** Registrere hva Rolf valgte (sendes tilbake som laeringsdata)

## Kontrakt B (din input)

Se /shared/kontrakt-b.json — dette faar du fra Spor 2 (Motor).
Inneholder: situasjonsoppsummering, anbefaling, andre alternativer med ankomsttid.

## Visningsregler

En notifikasjon viser alltid:
1. **Situasjon** — kort forklaring av hva som skjer
2. **Anbefaling** — en tydelig anbefalt handling, fremhevet visuelt
3. **Alternativer** — andre valg med estimert ankomsttid hjem

Reisevaermelding:
- Vises periodisk foer vanlig avreisetid
- Pent vaaer (ingen avvik): kort bekreftelse ("Reisen ser bra ut")
- Daarlig vaaer (avvik): anbefaling med alternativer

## Avgrensning

- Du henter IKKE data — det gjoer Spor 1
- Du analyserer IKKE avvik — det gjoer Spor 2
- Du viser det Spor 2 leverer via Kontrakt B
- Bruk mock-data fra /shared til backend er klar
