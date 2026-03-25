# Motor-design: Vurdering og anbefaling

## Utgangspunkt

Data-laget (`/data`) leverer allerede et rikt datagrunnlag i Kontrakt A.
Motor trenger ikke bygge egen historikklagring — konteksten er der.

## Tilgjengelig datagrunnlag

| Data | Kjelde | Kva det gir oss |
|---|---|---|
| `avvik[]` | SIRI-SX via Journey Planner | Aktive avvik med alvorlegheit, linjer, stasjonar |
| `reisealternativer[]` | Journey Planner v3 | 5 alternativ med status (i rute/forsinket/innstilt) |
| `sanntidsdata.faktiske_ankomster` | invalid-ET / historiske reiser | Faktiske forseinkingar siste 2 timar |
| `sanntidsdata.forsinkelsesstatistikk` | Berekna per linje/time | Median + p90 forseinking |
| `sanntidsdata.innstillinger` | Avgangstavle + reisedata | Heile/delvise innstillingar |
| `bildata` | OSRM + Vegvesen Trafikkdata | Kjoeyretid med trafikk, E18-kapasitet |
| `bruker.preferanser.laert[]` | Brukerprofil | Kva Rolf har valt tidlegare |

## Prosesseringsflyt

```
Kontrakt A inn
    |
    +-- 1. KLASSIFISER (rein regelkode, ~5ms)
    |       avvik[] ikkje tom?                → type = "avvik"
    |       innstilling paa Rolfs linje?      → type = "avvik"
    |       forsinkelse > 5 min paa avgang?   → type = "avvik"
    |       p90 forhoeya for linje/time?      → type = "vaermelding" (med merknad)
    |       alt i rute                        → type = "vaermelding"
    |
    +-- 2. BERIK MED KONTEKST (data finst allereie)
    |       forsinkelsesstatistikk
    |         → "RE11 har p90 paa 8.5 min kl 16 — upaaliteleg"
    |       bildata
    |         → "Bil tar 44 min, E18 er 16% over normalt"
    |       laert[]
    |         → "Rolf vel 'reis tidlegare' ved signalfeil (3 gonger)"
    |       innstillinger
    |         → "RE11 kl 16:42 er innstilt"
    |
    +-- 3. RANGER ALTERNATIV (regel + preferansar)
    |       a) Fjern innstilte alternativ (eller marker tydeleg)
    |       b) Sorter etter estimert ankomst heim
    |       c) Boost handlingar Rolf har valt foer:
    |          - laert[].valgt_handling == "reis_tidlegare" → +vekt
    |          - laert[].antall_gonger hoeyre → sterkare boost
    |       d) Legg til bil som alternativ viss relevant:
    |          - bildata.estimert_reisetid_min < beste tog-alternativ
    |          - eller alle togalternativ er innstilt/kraftig forseinka
    |       e) Vel topp-1 som anbefaling, resten som andre_alternativ
    |
    +-- 4. GENERER TEKST
    |       Avviksvarsel → Claude API (eitt kall)
    |         Input:  situasjon + rangerte alternativ + preferansar + statistikk
    |         Output: oppsummering + anbefalingstekst paa norsk
    |       Vaermelding → Mal (ingen API-kall)
    |         "Heimreisa ser bra ut. {linje} kl {tid} er i rute."
    |
    +-- 5. BYGG KONTRAKT B
            type: "avvik" eller "vaermelding"
            situasjon.oppsummering (fraa steg 4)
            anbefaling (topp-1 fraa steg 3)
            andre_alternativ (resten fraa steg 3)
```

## Klassifiseringsreglar (steg 1)

```python
def klassifiser(kontrakt_a):
    avvik = kontrakt_a["avvik"]
    alternativer = kontrakt_a["reisealternativer"]
    innstillinger = kontrakt_a["sanntidsdata"]["innstillinger"]
    stats = kontrakt_a["sanntidsdata"]["forsinkelsesstatistikk"]

    # Hoeg prioritet: aktive avvik
    if avvik:
        return "avvik", max(a["alvorlighet"] for a in avvik)

    # Hoeg prioritet: innstilling paa brukarens linjer
    bruker_linjer = extract_bruker_linjer(alternativer)
    if any(i["linje"] in bruker_linjer for i in innstillinger):
        return "avvik", "hoy"

    # Middels prioritet: forsinkelse over terskel
    forsinkede = [a for a in alternativer if a["status"] == "forsinket"]
    if forsinkede:
        return "avvik", "middels"

    # Lav prioritet: historisk upaalitelegheit
    hoey_p90 = [s for s in stats if s["p90_forsinkelse_min"] > 10]
    if hoey_p90:
        return "vaermelding", "lav"  # med merknad

    return "vaermelding", "ingen"
```

## Rangeringslogikk (steg 3)

```python
def ranger(alternativer, bildata, laert):
    # Fjern innstilte
    gyldige = [a for a in alternativer if a["status"] != "innstilt"]

    # Sorter paa ankomsttid
    gyldige.sort(key=lambda a: a["estimert_ankomst"])

    # Boost basert paa laerte preferansar
    for alt in gyldige:
        handling = gjett_handling(alt)  # "reis_tidlegare", "alternativ_rute", etc.
        for pref in laert:
            if pref["valgt_handling"] == handling:
                alt["_boost"] = pref["antall_gonger"]

    # Legg til bil viss relevant
    if bildata and skal_foreslaa_bil(bildata, gyldige):
        gyldige.append(bygg_bil_alternativ(bildata))

    # Sorter endeleg: ankomsttid + boost
    gyldige.sort(key=lambda a: (a["estimert_ankomst"], -a.get("_boost", 0)))

    return gyldige[0], gyldige[1:]  # anbefaling, andre
```

## Tekstgenerering (steg 4)

### Avviksvarsel — Claude API

Eitt kall med strukturert prompt:

```
Du er ein reiseassistent for ein pendlar (Drammen <-> Oslo).
Skriv kort og tydeleg paa norsk.

SITUASJON:
- Avvik: {avvik_beskrivelse}
- Alvorlegheit: {alvorlighet}
- Statistikk: {p90_data}

ANBEFALING:
- Beste alternativ: {topp_alternativ}
- Andre alternativ: {resten}
- Bilalternativ: {bildata_oppsummering}

ROLFS PREFERANSAR:
- Tidlegare val: {laert_oppsummering}

Skriv:
1. Ein kort oppsummering av situasjonen (1-2 setningar)
2. Ein tydeleg anbefaling (kva Rolf boer gjoere)
```

### Vaermelding — Malar (ingen API-kall)

```python
MALAR = {
    "ingen": "Heimreisa ser bra ut. {linje} kl {tid} er i rute.",
    "lav": "Heimreisa ser bra ut, men {linje} har vore noko forseinka i dag "
           "(median {median} min). {linje} kl {tid} er i rute no.",
}
```

Sparer Claude API-kall paa ~90% av dagane (normaldagar).

## Bil som alternativ

Data-laget gir `bildata` med:
- Kjoeyretid utan trafikk (OSRM): ~39 min
- Estimert med trafikk: ~44 min
- E18-kapasitetsutnytting per maalepunkt

Motor foreslaar bil naar:
- Alle togalternativ er innstilt
- Beste tog-ankomst er > 30 min seinare enn bil
- E18-kapasitet er under 1.3 (ikkje fullt kaos)

## Eksempel: Avviksvarsel

**Input (Kontrakt A):**
- Avvik: Signalfeil ved Asker, hoey alvorlegheit
- Alt-1: RE11 kl 16:31, i rute (ankomst 17:19)
- Alt-3: RE11 kl 16:42, forseinka (ankomst 17:50)
- Statistikk: RE11 p90 = 8.5 min kl 16
- Bil: 44 min (E18 kapasitet 1.16)
- Laert: "reis_tidlegare" ved signalfeil (3 gonger)

**Output (Kontrakt B):**
```json
{
  "type": "avvik",
  "situasjon": {
    "oppsummering": "Signalfeil ved Asker. RE11 har vore upaaliteleg i ettermiddag (p90: 8.5 min). Seinare avgangar kan bli innstilt.",
    "alvorlighet": "hoy",
    "avvik_ids": ["sx-12345"]
  },
  "anbefaling": {
    "handling": "reis_tidligere",
    "beskrivelse": "Ta RE11 kl 16:31 fraa Nationaltheatret. Du er heime ca. 17:19.",
    "alternativ_id": "alt-1",
    "estimert_ankomst_hjem": "2026-03-25T17:19:49+01:00"
  },
  "andre_alternativer": [
    {
      "handling": "alternativ_rute",
      "beskrivelse": "Bil via E18 — ca. 44 min. Trafikken er noko over normalt.",
      "alternativ_id": null,
      "estimert_ankomst_hjem": "2026-03-25T17:25:00+01:00"
    },
    {
      "handling": "utsett",
      "beskrivelse": "Vent paa RE11 kl 16:42, men rekn med forseinking (ankomst ~17:50).",
      "alternativ_id": "alt-3",
      "estimert_ankomst_hjem": "2026-03-25T17:50:00+01:00"
    }
  ]
}
```

## Eksempel: Vaermelding (normal dag)

**Input:** Ingen avvik, alle i rute, p90 = 0 min, bil 39 min.

**Output:**
```json
{
  "type": "vaermelding",
  "situasjon": {
    "oppsummering": "Heimreisa ser bra ut. RE11 kl 16:31 er i rute.",
    "alvorlighet": "ingen"
  },
  "anbefaling": {
    "handling": "reis_som_normalt",
    "beskrivelse": "Ta RE11 kl 16:31 fraa Nationaltheatret som vanleg.",
    "alternativ_id": "alt-1",
    "estimert_ankomst_hjem": "2026-03-25T17:19:49+01:00"
  },
  "andre_alternativer": []
}
```
