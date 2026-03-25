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
| `bildata.reisetid_fri_flyt_min` | Kjoeretid uten trafikk (OSRM) | OSRM public demo |
| `bildata.avstand_km` | Kjoereavstand | OSRM public demo |
| `bildata.trafikk_punkter[]` | Trafikkvolum ved 5 E18-stasjoner | Vegvesen Trafikkdata API |
| `bildata.estimert_reisetid_min` | Trafikkjustert kjoeretid (fri-flyt * snitt kapasitetsutnyttelse) | Beregnet fra OSRM + Trafikkdata |
| `bildata.kilde` | Datakilder brukt | Alltid `"osrm+vegvesen_trafikkdata"` |
| `vaerdata.tidspunkt` | Nærmeste prognosetidspunkt til avgang | MET.no Locationforecast 2.0 |
| `vaerdata.lufttemperatur_c` | Lufttemperatur i °C | MET.no Locationforecast 2.0 |
| `vaerdata.vindstyrke_ms` | Vindstyrke i m/s | MET.no Locationforecast 2.0 |
| `vaerdata.nedbor_neste_time_mm` | Nedbør neste time i mm (null hvis utilgjengelig) | MET.no Locationforecast 2.0 |
| `vaerdata.symbolkode` | Yr-symbolkode (f.eks. "cloudy", "rain", "clearsky_day") | MET.no Locationforecast 2.0 |
| `vaerdata.kilde` | Datakilde | Alltid `"met.no/locationforecast/2.0"` |

## Hva motoren boer bruke dette til

### Kollektivtransport
1. **Er Rolfs reise truet?** Se `reisealternativer[].status` + `avvik[]`
2. **Hvor forsinket er linjene egentlig?** Se `sanntidsdata.forsinkelsesstatistikk` — median og p90 gir et bilde utover enkeltavganger
3. **Er det et moenster av kanselleringer?** Se `sanntidsdata.innstillinger` — flere kanselleringer paa samme linje = hoey risiko
4. **Hva skjedde de siste 2 timene?** Se `sanntidsdata.faktiske_ankomster` — nylige forsinkelser predikerer kommende forsinkelser
5. **Avviksmeldinger for kontekst:** Se `avvik[]` for aa forstaa *hvorfor* ting er forsinket (signalfeil, sporveksel, etc.)

### Evaluering av reisealternativer ved innstilling eller kraftig forsinkelse

Naar ett eller flere alternativer er innstilt eller kraftig forsinket, maa motoren gi en tydelig anbefaling. Slik brukes dataene til aa evaluere og rangere:

**Steg 1 — Identifiser trusselen:**
- Sjekk `reisealternativer[].status`: `"innstilt"` = bekreftet kansellert, `"forsinket"` = forsinket (sjekk omfang)
- Kryssreferér med `avvik[]`: avvik med `alvorlighet: "hoy"` som `paavirker_linjer` overlapper med alternativets linjer betyr hoey risiko
- Sjekk `sanntidsdata.innstillinger[]`: dersom alternativets `steg[].linje` finnes her med `type: "hel_tur"`, er hele avgangen borte

**Steg 2 — Vurder gjenvaerende alternativer:**
- Filtrer bort alternativer med `status: "innstilt"`
- For alternativer med `status: "forsinket"`, estimer faktisk forsinkelse:
  - Se `sanntidsdata.forsinkelsesstatistikk[]` for linjen — `p90_forsinkelse_min` gir worst-case
  - Se `sanntidsdata.faktiske_ankomster[]` for nylige avganger paa samme linje — dersom de siste 2-3 avgangene var 15+ min forsinket, forvent det samme
- Ranger gjenvaerende alternativer etter `estimert_ankomst` + eventuell forventet forsinkelse

**Steg 3 — Evaluer bil som alternativ:**
- Dersom alle kollektivalternativer er innstilt eller har p90 forsinkelse >20 min:
  - Sammenlign `bildata.estimert_reisetid_min` med beste gjenvaerende kollektivalternativ
  - Sjekk `bildata.trafikk_punkter[].kapasitetsutnyttelse` — verdier >1.3 betyr koe, bil er kanskje ikke bedre
  - Dersom bil er raskere OG E18 ikke er overfylt, anbefal bil som alternativ

**Steg 4 — Hensyn til vaer:**
- Dersom `vaerdata.nedbor_neste_time_mm` >2.0 eller `vaerdata.vindstyrke_ms` >10: kjoereforhold kan vaere daarlige — vekt dette i bil-anbefalingen
- Kraftig nedbor oeker ogsaa risiko for ytterligere togforsinkelser

**Steg 5 — Bygg anbefalingen:**
- Velg det beste alternativet basert paa steg 2-4
- Sett `anbefaling.handling` til riktig verdi:
  - `"reis_tidligere"` — dersom et tidligere alternativ fortsatt gaar i rute
  - `"alternativ_rute"` — dersom en annen linje/buss fungerer
  - `"utsett"` — dersom avviket er midlertidig og `avvik[].estimert_varighet_min` tilsier at normalt alternativ snart fungerer igjen
  - `"ikke_reis"` — dersom alle alternativer er innstilt og bil ogsaa er upraktisk
- Fyll alltid `andre_alternativer[]` med de oevrige mulighetene, inkludert bil og «vent»

**Eksempel — signalfeil med innstilt tog:**
```
reisealternativer[0].status = "i_rute"       → Tidlig tog kl 15:02, fortsatt ok
reisealternativer[1].status = "innstilt"      → Buss 31-rute, kansellert
reisealternativer[2].status = "forsinket"     → Vanlig tog kl 16:42, p90 forsinkelse 25 min

avvik[0].alvorlighet = "hoy", paavirker_linjer = ["L1", "RE11"]
bildata.estimert_reisetid_min = 44, trafikk ok (kapasitetsutnyttelse ~1.1)

→ Anbefaling: "reis_tidligere" (alt-0, kl 15:02)
→ Andre: bil (44 min), forsinket tog (ankomst ~18:05), vent (avvik løst om ~1t)
```

### Vær
9. **Bør Rolf kle seg annerledes?** Se `vaerdata.lufttemperatur_c` og `vaerdata.nedbor_neste_time_mm`. Nedbør >0.5 mm/t eller temperatur <0 °C kan være verdt å nevne.
10. **Symbolkode for UI:** `vaerdata.symbolkode` kan brukes direkte mot Yr-ikoner. Se https://api.met.no/weatherapi/weathericon/2.0/documentation for mapping.
11. **Er været relevant for reisevalg?** Sterk vind (>10 m/s) eller kraftig nedbør kan påvirke om Rolf bør velge bil fremfor tog/buss.

### Bil vs. tog (nytt)
6. **Boer Rolf kjoere?** Sammenlign `bildata.estimert_reisetid_min` med `reisealternativer[].estimert_ankomst - avgang`. Dersom bil er raskere OG togene har forsinkelser/kanselleringer, kan motoren anbefale aa kjoere.
7. **Er E18 uvanlig trafikkert?** Se `bildata.trafikk_punkter[].kapasitetsutnyttelse`. Verdier >1.2 tyder paa koe. Verdier <0.8 betyr roligere enn vanlig.
8. **Merk:** `estimert_reisetid_min` kan vaere `null` dersom trafikkdata ikke er tilgjengelig (f.eks. nattestid). Da bruk `reisetid_fri_flyt_min` som nedre grense.

## Typede modeller

Alle datastrukturer er definert som `TypedDict` i `data/models.py`. Motoren kan importere disse for typesjekking:

```python
from data.models import KontraktAUtvidet, Sanntidsdata, FaktiskAnkomst, Bildata, TrafikkPunkt, Vaerdata
```

## Avhengigheter

```bash
pip install httpx  # async HTTP client (eneste eksterne avhengighet)
```

## Begrensninger

- Bruker er hardkodet (Rolf, Drammen ↔ Oslo). Profilen ligger i `data/bruker.py`.
- invalid-ET API kan feile — da faller vi tilbake til estimerte tider fra Journey Planner (noe lavere presisjon).
- Forsinkelsesstatistikk er basert paa 2 timers vindu, ikke historisk — gir et oeyeblikksbilde, ikke langtidstrend.
- Vegvesen Trafikkdata har ~3 timers lag. Vi bruker siste tilgjengelige time, ikke naavaerende time.
- Bil-estimatet bruker trafikkvolum som koe-proxy — dette korrelerer godt i rushtid men er mindre presist ellers.
- OSRM er en offentlig demo-server uten SLA. For produksjon boer vi bruke en self-hosted OSRM eller kommersiell API.
- Én E18-stasjon (Drammensv v/Maritim) rapporterer ikke alltid data — den faar `kapasitetsutnyttelse: 1.0` som fallback.- Værdata hentes fra MET.no Locationforecast 2.0 (gratis, krever User-Agent). Prognosen nærmest avgangsøyeblikket brukes — presisjon avhenger av hvor langt frem i tid avgangen er.