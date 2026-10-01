"""FastAPI-app. Het contract met de frontend staat in docs/api.md."""

import sqlite3
from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import db
from .config import instellingen
from .dictee import AIFout, ClaudeZinnenBron, ZinnenBron, genereer_dictee
from .woordenlijst import OngeldigeLijst, lees_csv, week_uit_bestandsnaam


@asynccontextmanager
async def levensduur(app: FastAPI):
    db.initialiseer(instellingen.database_pad)
    yield


app = FastAPI(title="Chinees leren", lifespan=levensduur)
app.add_middleware(
    CORSMiddleware,
    allow_origins=instellingen.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = db.verbind(instellingen.database_pad)
    try:
        yield conn
    finally:
        conn.close()


def get_zinnen_bron() -> ZinnenBron:
    if not instellingen.anthropic_api_key:
        raise HTTPException(503, "De AI is niet beschikbaar: ANTHROPIC_API_KEY ontbreekt in .env.")
    return ClaudeZinnenBron(instellingen.anthropic_api_key, instellingen.claude_model)


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


# --- Modellen (vorm zoals in docs/api.md) -------------------------------------


class Woord(BaseModel):
    id: int
    hanzi: str
    pinyin: str
    betekenis: str
    week: int


class WeekSamenvatting(BaseModel):
    nummer: int
    titel: str | None
    aantal_woorden: int
    geupload_op: str


class Week(WeekSamenvatting):
    woorden: list[Woord]


class Zin(BaseModel):
    nr: int
    hanzi: str
    pinyin: str
    vertaling: str
    woorden_van_de_week: list[str]
    onbekende_tekens: list[str]


class Dictee(BaseModel):
    id: int
    week: int
    aangemaakt_op: str
    zinnen: list[Zin]
    waarschuwingen: list[str]


class DicteeSamenvatting(BaseModel):
    id: int
    week: int
    aangemaakt_op: str
    aantal_zinnen: int


class DicteeAanvraag(BaseModel):
    week: int
    aantal_zinnen: int = Field(5, ge=1, le=15)


# --- Algemeen ----------------------------------------------------------------


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_beschikbaar": bool(instellingen.anthropic_api_key)}


# --- Weken & woorden -----------------------------------------------------------


@app.post("/api/weken", status_code=201, response_model=Week)
async def upload_week(
    conn: Conn,
    bestand: Annotated[UploadFile, File()],
    nummer: Annotated[int | None, Form(ge=1)] = None,
    titel: Annotated[str | None, Form()] = None,
    vervang: Annotated[bool, Form()] = False,
):
    nummer = nummer or week_uit_bestandsnaam(bestand.filename)
    if nummer is None:
        raise HTTPException(
            422, "Geen weeknummer: geef 'nummer' mee of noem het bestand bv. week-03.csv."
        )
    try:
        woorden = lees_csv(await bestand.read())
    except OngeldigeLijst as e:
        raise HTTPException(422, str(e))
    if db.week_bestaat(conn, nummer) and not vervang:
        raise HTTPException(409, f"Week {nummer} bestaat al. Stuur vervang=true om te vervangen.")

    db.sla_week_op(conn, nummer, (titel or "").strip() or None, woorden)
    return db.haal_week(conn, nummer)


@app.get("/api/weken", response_model=list[WeekSamenvatting])
def lijst_weken(conn: Conn):
    return db.lijst_weken(conn)


@app.get("/api/weken/{nummer}", response_model=Week)
def haal_week(nummer: int, conn: Conn):
    week = db.haal_week(conn, nummer)
    if week is None:
        raise HTTPException(404, f"Week {nummer} bestaat niet.")
    return week


@app.delete("/api/weken/{nummer}", status_code=204)
def verwijder_week(nummer: int, conn: Conn):
    if not db.verwijder_week(conn, nummer):
        raise HTTPException(404, f"Week {nummer} bestaat niet.")
    return Response(status_code=204)


@app.get("/api/woorden", response_model=list[Woord])
def lijst_woorden(conn: Conn, tot_week: Annotated[int | None, Query()] = None):
    return db.haal_woorden(conn, tot_week=tot_week)


# --- Dictees -------------------------------------------------------------------


@app.post("/api/dictees", status_code=201, response_model=Dictee)
def maak_dictee(
    aanvraag: DicteeAanvraag,
    conn: Conn,
    bron: Annotated[ZinnenBron, Depends(get_zinnen_bron)],
):
    if not db.week_bestaat(conn, aanvraag.week):
        raise HTTPException(404, f"Week {aanvraag.week} bestaat niet.")
    alle = db.haal_woorden(conn, tot_week=aanvraag.week)
    weekwoorden = [w for w in alle if w["week"] == aanvraag.week]
    bekend = [w for w in alle if w["week"] != aanvraag.week]

    try:
        zinnen, waarschuwingen = genereer_dictee(bron, weekwoorden, bekend, aanvraag.aantal_zinnen)
    except AIFout as e:
        raise HTTPException(502, str(e))
    if not zinnen:
        raise HTTPException(502, "De AI gaf geen zinnen terug. Probeer het opnieuw.")

    dictee_id = db.sla_dictee_op(conn, aanvraag.week, zinnen, waarschuwingen)
    return db.haal_dictee(conn, dictee_id)


@app.get("/api/dictees", response_model=list[DicteeSamenvatting])
def lijst_dictees(conn: Conn, week: Annotated[int | None, Query()] = None):
    return db.lijst_dictees(conn, week)


@app.get("/api/dictees/{dictee_id}", response_model=Dictee)
def haal_dictee(dictee_id: int, conn: Conn):
    dictee = db.haal_dictee(conn, dictee_id)
    if dictee is None:
        raise HTTPException(404, f"Dictee {dictee_id} bestaat niet.")
    return dictee


@app.delete("/api/dictees/{dictee_id}", status_code=204)
def verwijder_dictee(dictee_id: int, conn: Conn):
    if not db.verwijder_dictee(conn, dictee_id):
        raise HTTPException(404, f"Dictee {dictee_id} bestaat niet.")
    return Response(status_code=204)
