# Pendlerkompis

KI-drevet reiseassistent som proaktivt varsler dagpendlere om avvik og gir personlige anbefalinger med konkrete alternativer.

## Konsept

Pendlerkompis kjenner reisemonsteret ditt og varsler deg om avvik med konkrete alternativer -- for du gar ut dora.

### Brukerreise

1. **Oppstart** -- Oppgi hjem, jobb og avreisetider
2. **Avvik** -- Notifikasjon med anbefaling og alternativer
3. **Laering** -- Systemet fanger opp hva du valgte og blir smartere over tid
4. **Reisevaermelding** -- Periodisk status for reisen din, uansett avvik

### Persona: Erfarne Rolf

Dagpendler Drammen <-> Oslo. Kjenner reisen sin godt, men trenger beslutningsstotte ved avvik: reise tidligere, utsette, alternativ rute, eller jobbe hjemmefra.

## Arkitektur

Tre spor i en pipeline:

```
Data inn --> Motor (analyse/KI) --> Presentasjon
```

- **Spor 1: Data inn** -- Entur API-er (SIRI-SX, sanntid, JourneyPlanner) + brukerprofil
- **Spor 2: Motor** -- Analyse, KI-tolkning (Claude API), anbefalinger
- **Spor 3: Presentasjon** -- Frontend/UI, varsler, onboarding

## Prosjektstruktur

```
/data            # Spor 1: Datahenting og brukerprofil
/motor           # Spor 2: Analyse og KI
/presentasjon    # Spor 3: Frontend/UI
/shared          # Kontrakter og mock-data
```

## Team

7 personer, 5 utviklere. Hackaton 2026.
