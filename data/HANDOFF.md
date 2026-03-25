# Spor 1 → Spor 2 Handoff: Data til Motor

## Hva datalaget leverer

Datalaget henter sanntidsdata fra Enturs API-er og returnerer en **utvidet Kontrakt A** som JSON. Skjemaet er definert i `shared/kontrakt-a.json`, eksempeldata i `shared/mock-kontrakt-a.json`.

## Hvordan kalle datalaget

### Fra Python (anbefalt integrasjon)

```python
import asyncio
from data.main import hent_pendlerdata

# Hent data for hjemreise kl 16:30
result = asyncio.run(hent_pendlerdata(direction="fra_jobb"))

# Eller med egendefinert tid
result = asyncio.run(hent_pendlerdata(direction="fra_hjem", override_time="07:15"))
```

`result` er en Python-dict som matcher `KontraktAUtvidet` (se `data/models.py`).

### Fra CLI (for testing/debugging)

```bash
cd pendlerkompis
PYTHONPATH=. .venv/bin/python -m data.main --direction fra_jobb
PYTHONPATH=. .venv/bin/python -m data.main --direction fra_hjem --time 07:15
```

Skriver JSON til stdout.

## Hva output inneholder

| Felt | Innhold | Kilde |
|------|---------|-------|
| `bruker` | Rolf sin profil (rute, preferanser) | `data/bruker.py` |
| `avvik[]` | Avviksmeldinger (SIRI-SX) | Journey Planner `situations` |
| `reisealternativer[]` | Reiseforslag med status | Journey Planner `trip` |
| `sanntidsdata.faktiske_ankomster[]` | Ankomster siste 2t, samme linjer+destinasjon | invalid-ET API (fallback: historiske trip-data) |
| `sanntidsdata.forsinkelsesstatistikk[]` | Median og p90 forsinkelse per linje/time | Beregnet fra faktiske_ankomster |
| `sanntidsdata.innstillinger[]` | Kanselleringer (hel tur / enkelt stopp) | Trip-data + quay avgangstavle |

## Hva motoren bor bruke dette til

1. **Er Rolfs reise truet?** Se `reisealternativer[].status` + `avvik[]`
2. **Hvor forsinket er linjene egentlig?** Se `sanntidsdata.forsinkelsesstatistikk` — median og p90 gir et bilde utover enkeltavganger
3. **Er det et moenster av kanselleringer?** Se `sanntidsdata.innstillinger` — flere kanselleringer paa samme linje = hoey risiko
4. **Hva skjedde de siste 2 timene?** Se `sanntidsdata.faktiske_ankomster` — nylige forsinkelser predikerer kommende forsinkelser
5. **Avviksmeldinger for kontekst:** Se `avvik[]` for aa forstaa *hvorfor* ting er forsinket (signalfeil, sporveksel, etc.)

## Typede modeller

Alle datastrukturer er definert som `TypedDict` i `data/models.py`. Motoren kan importere disse for typesjekking:

```python
from data.models import KontraktAUtvidet, Sanntidsdata, FaktiskAnkomst
```

## Avhengigheter

```bash
pip install httpx  # async HTTP client (eneste eksterne avhengighet)
```

## Begrensninger

- Bruker er hardkodet (Rolf, Drammen ↔ Oslo). Profilen ligger i `data/bruker.py`.
- invalid-ET API kan feile — da faller vi tilbake til estimerte tider fra Journey Planner (noe lavere presisjon).
- Forsinkelsesstatistikk er basert paa 2 timers vindu, ikke historisk — gir et oeyeblikksbilde, ikke langtidstrend.
