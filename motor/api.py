"""Pendlerkompis motor API — HTTP-server for Spor 3 (Presentasjon).

Eksponerer Kontrakt B via HTTP.

Start:
    cd pendlerkompis
    PYTHONPATH=. uvicorn motor.api:app --reload --port 8082

Endepunkter:
    GET  /anbefaling?direction=fra_jobb          → Kontrakt B
    GET  /anbefaling?direction=fra_jobb&mock=1   → Kontrakt B fra mock-data
    POST /feedback                               → Logg brukerens valg (læring)
    GET  /helse                                  → Helsesjekk
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Pendlerkompis Motor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enkel in-memory logg av brukervalg (for læringsloop)
_feedback_log: list[dict] = []


@app.get("/helse")
def helse():
    return {"status": "ok", "tidspunkt": datetime.now().isoformat()}


@app.get("/anbefaling")
async def anbefaling(
    direction: str = Query("fra_jobb", pattern="^(fra_hjem|fra_jobb)$"),
    time: str | None = Query(None, description="Override avreisetid HH:MM"),
    mock: bool = Query(False, description="Bruk mock-data"),
    verbose: bool = Query(False),
):
    """Hent anbefaling for Rolf. Returnerer Kontrakt B."""
    try:
        from motor.main import generate_recommendation, generate_recommendation_from_mock

        if mock:
            result = await generate_recommendation_from_mock(verbose=verbose)
        else:
            result = await generate_recommendation(direction, time, verbose=verbose)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FeedbackBody(BaseModel):
    bruker_id: str
    valgt_handling: str
    alternativ_id: str | None = None
    situasjon_type: str | None = None
    kommentar: str | None = None


@app.post("/feedback")
def feedback(body: FeedbackBody):
    """Registrer Rolfs valg — brukes til å forbedre fremtidige anbefalinger."""
    entry = {
        "tidspunkt": datetime.now().isoformat(),
        **body.model_dump(),
    }
    _feedback_log.append(entry)

    # Skriv til fil for persistens
    log_path = Path(__file__).parent / "feedback.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {"status": "lagret", "antall_totalt": len(_feedback_log)}


@app.get("/feedback")
def hent_feedback():
    """Hent logg over brukervalg."""
    return {"valg": _feedback_log}
