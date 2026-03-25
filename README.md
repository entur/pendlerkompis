# Pendlerkompis

KI-drevet reiseassistent som proaktivt varsler dagpendlere om avvik og gir personlige anbefalinger med konkrete alternativer.

## Konsept

Pendlerkompis kjenner reisemønsteret ditt og varsler deg om avvik med konkrete alternativer — før du går ut døra.

### Brukerreise

1. **Oppstart** — Oppgi hjem, jobb og avreisetider
2. **Avvik** — Notifikasjon med anbefaling og alternativer
3. **Læring** — Systemet fanger opp hva du valgte og blir smartere over tid
4. **Reiseværmelding** — Periodisk status for reisen din, uansett avvik

### Persona: Rutinerte Rolf

![Rutinerte Rolf](docs/rutinerte_rolf.png)

Dagpendler Drammen <-> Oslo. Kjenner reisen sin godt, men trenger beslutningsstøtte ved avvik: reise tidligere, utsette, alternativ rute, eller jobbe hjemmefra.

## Arkitektur

Tre spor i en pipeline:

```
Data inn --> Motor (analyse/KI) --> Presentasjon
```

- **Spor 1: Data inn** — Entur API-er (SIRI-SX, sanntid, JourneyPlanner) + brukerprofil
- **Spor 2: Motor** — Analyse, KI-tolkning (Claude API), anbefalinger
- **Spor 3: Presentasjon** — Frontend/UI, varsler, onboarding

## Prosjektstruktur

```
/data            # Spor 1: Datahenting og brukerprofil
/motor           # Spor 2: Analyse og KI
/presentasjon    # Spor 3: Frontend/UI
/shared          # Kontrakter og mock-data
```

## Team

7 personer, 5 utviklere. Hackaton 2026.
