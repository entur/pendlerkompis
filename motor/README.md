# Motor (Spor 2)

All backend-logikk for Pendlerkompis. Tek imot reisedata (Kontrakt A) og leverer ferdig tolka anbefaling (Kontrakt B).

## Kjoering

```bash
# Fraa prosjektrot:
export ANTHROPIC_API_KEY=<din noekkel>
npm run motor:jobb         # Heimreise fraa jobb
npm run motor:hjem         # Reise fraa heimen

# Eller direkte:
PYTHONPATH=. .venv/bin/python -m motor.main --direction fra_jobb [--time 16:30]
```

## Arkitektur

```
data.main.hent_pendlerdata()
    |
    v
Kontrakt A (bruker + avvik + alternativer + sanntidsdata + bildata)
    |
    +-- klassifiser.py    Avvik eller vaermelding? (regelbasert)
    |
    +-- ranger.py         Sorter, boost preferansar, vurder bil
    |
    +-- tekst.py          Claude API (avvik) / malar (vaermelding)
    |
    v
Kontrakt B (anbefaling + alternativer til presentasjon)
```

## Moduler

| Fil | Ansvar |
|---|---|
| `main.py` | Orkestrer heile pipelinen, CLI-inngang |
| `klassifiser.py` | Avgjer type (avvik/vaermelding) og alvorlegheit |
| `ranger.py` | Rangerer alternativ, booster laerte preferansar, legg til bil |
| `tekst.py` | Genererer norsk tekst — Claude API for avvik, malar for normaldagar |
| `models.py` | TypedDict-definisjonar for Kontrakt B |

## Klassifiseringsreglar

| Signal | Resultat |
|---|---|
| Aktive avvik (SIRI-SX) | `avvik` + hoeyaste alvorlegheit |
| Innstilling paa brukarens linje | `avvik` + `hoy` |
| Forseinka alternativ | `avvik` + `middels` |
| p90 > 10 min for linje/time | `vaermelding` + `lav` |
| Alt i rute | `vaermelding` + `ingen` |

## Rangeringslogikk

1. Fjern innstilte alternativ
2. Sorter paa estimert ankomst heim
3. Boost handlingar Rolf har valt foer (`laert[]`)
4. Legg til bil viss relevant (raskare, eller alt innstilt)
5. Topp-1 = anbefaling, resten = andre alternativ

## Tekstgenerering

- **Avvik:** Eitt Claude API-kall med situasjon, statistikk, alternativ og preferansar
- **Vaermelding:** Mal-basert, ingen API-kall — sparer kostnad paa ~90% av dagane

## Avhengigheiter

- `anthropic` — Claude API-klient
- `httpx` — (via data-laget)
- `ANTHROPIC_API_KEY` miljoevariabel

## Kontrakter

- **Input:** `/shared/kontrakt-a.json` (fraa data-laget)
- **Output:** `/shared/kontrakt-b.json` (til presentasjon)
- **Mock-data:** `/shared/mock-kontrakt-a.json` for testing
