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

## Kom i gang

### Krav

- Python 3.12+
- Node.js 18+ (for frontend)
- `ANTHROPIC_API_KEY` miljoevariabel (for motor ved avvik)

### Oppsett

```bash
# Installer Python-avhengigheiter (data + motor)
npm run setup

# Eller manuelt:
python3 -m venv .venv
.venv/bin/pip install -r data/requirements.txt -r motor/requirements.txt

# Installer frontend-avhengigheiter
npm run frontend:install
```

### Kjoer

```bash
# Hent raa reisedata (Kontrakt A)
npm run data:jobb          # Heimreise fraa jobb
npm run data:hjem          # Reise fraa heimen

# Kjoer motor — full pipeline med anbefaling (Kontrakt B)
export ANTHROPIC_API_KEY=<din noekkel>
npm run motor:jobb         # Heimreise fraa jobb
npm run motor:hjem         # Reise fraa heimen

# Start frontend
npm run frontend
```

Alle kommandoar aksepterer ekstra argument via `--`:

```bash
npm run motor -- --direction fra_jobb --time 16:30
```

### Eksempel-output (motor)

```json
{
  "bruker_id": "rolf-1",
  "type": "vaermelding",
  "situasjon": {
    "oppsummering": "Heimreisa ser bra ut. RE11 kl 16:30 er i rute.",
    "alvorlighet": "ingen"
  },
  "anbefaling": {
    "handling": "reis_som_normalt",
    "beskrivelse": "Ta RE11 kl 16:30 som vanleg.",
    "alternativ_id": "alt-1",
    "estimert_ankomst_hjem": "2026-03-25T17:19:49+01:00"
  }
}
```

## Team

7 personer, 5 utviklere. Hackaton 2026.
