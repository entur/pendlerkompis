# Innspill: Prosessering av reisedata for Rutinerte Rolf

## Utgangspunkt

Data-laget (`/data`) leverer Kontrakt A med:
- **Brukerprofil** (hjem, jobb, avreisetider, laerte preferanser)
- **Avvik** fra SIRI-SX (signalfeil, innstillinger, stenginger)
- **Reisealternativer** med sanntidsstatus (i rute / forsinket / innstilt)
- **Sanntidsdata** (faktiske ankomster, forsinkelsesstatistikk per linje/time, innstillinger)

Motor maa behandle dette slik at Rolf faar **relevant, handlingsbar informasjon** — ikke raadata.

## Tre hovedoppgaver

### 1. Vurdere: Er dette verdt aa si fra om?

Ikke alt er en varsling. Motor maa filtrere stoey.

| Signal fra data | Handling |
|---|---|
| Avvik paa Rolfs linjer (SX) | Varsle |
| Forsinkelse > 5 min paa hans avgang | Varsle |
| Innstilling paa hans avgang | Varsle |
| p90-forsinkelse hoey for linje/time | Nevne i vaermelding |
| Alt i rute, ingen avvik | Kort vaermelding |

**Prinsipp:** Ikke send en notifikasjon med mindre Rolf maa gjoere noe eller boer vite noe.

### 2. Rangere og anbefale

Naar det er avvik har data-laget allerede gitt oss alternativer. Motor maa:

- **Rangere** etter estimert ankomst hjem (Rolf vil hjem tidligst mulig)
- **Vekte** mot laerte preferanser (Rolf velger "reis tidligere" ved signalfeil)
- **Velge en anbefaling** + liste resten som alternativer
- **Bruke Claude API** til aa skrive en kort, naturlig oppsummering

### 3. Levere to moduser

**Avviksvarsel** (`"type": "avvik"`) — noe er galt:
```
"Du boer gaa naa. RE11 kl 16:31 fra Nationaltheatret er beste alternativ.
 Signalfeil ved Asker kan forsinke senere avganger."
```

**Reisevaermelding** (`"type": "vaermelding"`) — alt OK, eller lavt avvik:
```
"Hjemreisen ser bra ut. RE11 kl 16:31 er i rute.
 Siste 2 timer: 0 forsinkelser paa Drammen-linjene."
```

## Prosesseringsflyt

```
Kontrakt A inn
    |
    +-- 1. Klassifiser: avvik / forsinkelse / normalt
    |
    +-- 2. Relevansfilter: paavirker dette Rolfs neste avgang?
    |
    +-- 3. Rangeringslogikk:
    |       - Sorter alternativer etter ankomsttid
    |       - Boost basert paa laerte preferanser
    |       - Marker innstilte/forsinkede
    |
    +-- 4. Claude API:
    |       - Input: situasjon + alternativer + preferanser
    |       - Output: naturlig spraak-oppsummering
    |
    +-- 5. Bygg Kontrakt B
            - type: "avvik" eller "vaermelding"
            - anbefaling + alternativer med estimert ankomst
```

## Hva som gjoer dette verdifullt for Rolf

- **Proaktivt:** Han faar beskjed foer han staar paa perrongen
- **En anbefaling:** Ikke en liste aa tolke, men "gjoer dette"
- **Kontekst:** Sanntidsdata gir troverdighet ("siste 2t: 0 forsinkelser")
- **Laering:** Over tid tilpasses anbefalingene hans moenster

## Eksempel: Normal dag (ingen avvik)

Data-laget returnerer:
- `avvik: []`
- 5 alternativer, alle `"status": "i_rute"`
- Forsinkelsesstatistikk: 0 min median paa alle linjer

Motor leverer vaermelding:
```json
{
  "type": "vaermelding",
  "situasjon": {
    "oppsummering": "Alt ser bra ut for hjemreisen. RE11 kl 16:31 er i rute.",
    "alvorlighet": "lav"
  },
  "anbefaling": {
    "handling": "reis_som_normalt",
    "beskrivelse": "Ta RE11 kl 16:31 fra Nationaltheatret som vanlig.",
    "alternativ_id": "alt-1",
    "estimert_ankomst_hjem": "2026-03-25T17:19:49+01:00"
  }
}
```

## Eksempel: Signalfeil (avvik)

Data-laget returnerer:
- Avvik: signalfeil ved Asker, hoey alvorlighet
- Alt-1 i rute (tidlig avgang), Alt-3 forsinket
- Laert preferanse: "reis_tidligere" ved signalfeil (3 ganger)

Motor leverer avviksvarsel:
```json
{
  "type": "avvik",
  "situasjon": {
    "oppsummering": "Signalfeil ved Asker paavirker hjemreisen din. Senere tog kan bli forsinket.",
    "alvorlighet": "hoy"
  },
  "anbefaling": {
    "handling": "reis_tidligere",
    "beskrivelse": "Gaa fra jobb naa. Ta RE11 kl 15:02 fra Oslo S.",
    "alternativ_id": "alt-1",
    "estimert_ankomst_hjem": "2026-03-25T16:15:00+01:00"
  },
  "andre_alternativer": [
    {
      "handling": "alternativ_rute",
      "beskrivelse": "Buss 31 til Lysaker, tog videre til Drammen",
      "alternativ_id": "alt-2",
      "estimert_ankomst_hjem": "2026-03-25T18:00:00+01:00"
    },
    {
      "handling": "utsett",
      "beskrivelse": "Vent — feilen forventes loest innen kl 16. Reis som normalt.",
      "estimert_ankomst_hjem": "2026-03-25T17:50:00+01:00"
    }
  ]
}
```
