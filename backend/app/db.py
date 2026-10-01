"""SQLite-opslag. Bewust eenvoudig: één bestand, geen ORM."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS weken (
    nummer      INTEGER PRIMARY KEY,
    titel       TEXT,
    geupload_op TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS woorden (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    week      INTEGER NOT NULL REFERENCES weken(nummer) ON DELETE CASCADE,
    hanzi     TEXT NOT NULL,
    pinyin    TEXT NOT NULL,
    betekenis TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dictees (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    week           INTEGER NOT NULL REFERENCES weken(nummer) ON DELETE CASCADE,
    aangemaakt_op  TEXT NOT NULL,
    zinnen         TEXT NOT NULL,  -- JSON-lijst van Zin
    waarschuwingen TEXT NOT NULL,  -- JSON-lijst van strings
    resultaat      TEXT            -- JSON-lijst van ZinResultaat, NULL = nog niet nagekeken
);
"""


def nu() -> str:
    return datetime.now().isoformat(timespec="seconds")


def verbind(pad: Path) -> sqlite3.Connection:
    pad.parent.mkdir(parents=True, exist_ok=True)
    # Eén verbinding per request; FastAPI kan die in een andere thread gebruiken.
    conn = sqlite3.connect(pad, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialiseer(pad: Path) -> None:
    with verbind(pad) as conn:
        conn.executescript(SCHEMA)
        # Databases van vóór de resultaat-kolom bijwerken.
        kolommen = [r["name"] for r in conn.execute("PRAGMA table_info(dictees)")]
        if "resultaat" not in kolommen:
            conn.execute("ALTER TABLE dictees ADD COLUMN resultaat TEXT")
    conn.close()


# --- Weken & woorden ---------------------------------------------------------


def week_bestaat(conn: sqlite3.Connection, nummer: int) -> bool:
    return conn.execute("SELECT 1 FROM weken WHERE nummer = ?", (nummer,)).fetchone() is not None


def sla_week_op(
    conn: sqlite3.Connection, nummer: int, titel: str | None, woorden: list[dict]
) -> None:
    """Slaat een week op. Bestaat ze al, dan worden titel en woorden vervangen
    (de dictees van die week blijven bewaard)."""
    with conn:
        conn.execute(
            """
            INSERT INTO weken (nummer, titel, geupload_op) VALUES (?, ?, ?)
            ON CONFLICT (nummer) DO UPDATE SET titel = excluded.titel, geupload_op = excluded.geupload_op
            """,
            (nummer, titel, nu()),
        )
        conn.execute("DELETE FROM woorden WHERE week = ?", (nummer,))
        conn.executemany(
            "INSERT INTO woorden (week, hanzi, pinyin, betekenis) VALUES (?, ?, ?, ?)",
            [(nummer, w["hanzi"], w["pinyin"], w["betekenis"]) for w in woorden],
        )


def lijst_weken(conn: sqlite3.Connection) -> list[dict]:
    rijen = conn.execute(
        """
        SELECT w.nummer, w.titel, w.geupload_op, COUNT(wo.id) AS aantal_woorden
        FROM weken w LEFT JOIN woorden wo ON wo.week = w.nummer
        GROUP BY w.nummer ORDER BY w.nummer
        """
    ).fetchall()
    return [dict(r) for r in rijen]


def haal_week(conn: sqlite3.Connection, nummer: int) -> dict | None:
    for week in lijst_weken(conn):
        if week["nummer"] == nummer:
            week["woorden"] = haal_woorden(conn, alleen_week=nummer)
            return week
    return None


def verwijder_week(conn: sqlite3.Connection, nummer: int) -> bool:
    with conn:
        return conn.execute("DELETE FROM weken WHERE nummer = ?", (nummer,)).rowcount > 0


def haal_woorden(
    conn: sqlite3.Connection, tot_week: int | None = None, alleen_week: int | None = None
) -> list[dict]:
    sql = "SELECT id, hanzi, pinyin, betekenis, week FROM woorden"
    params: tuple = ()
    if alleen_week is not None:
        sql += " WHERE week = ?"
        params = (alleen_week,)
    elif tot_week is not None:
        sql += " WHERE week <= ?"
        params = (tot_week,)
    sql += " ORDER BY week, id"
    fouten = foutentelling(conn)
    return [
        {**dict(r), "keer_fout": fouten.get(r["hanzi"], 0)}
        for r in conn.execute(sql, params).fetchall()
    ]


# --- Dictees -----------------------------------------------------------------


def sla_dictee_op(
    conn: sqlite3.Connection, week: int, zinnen: list[dict], waarschuwingen: list[str]
) -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO dictees (week, aangemaakt_op, zinnen, waarschuwingen) VALUES (?, ?, ?, ?)",
            (
                week,
                nu(),
                json.dumps(zinnen, ensure_ascii=False),
                json.dumps(waarschuwingen, ensure_ascii=False),
            ),
        )
    return cur.lastrowid


def haal_dictee(conn: sqlite3.Connection, dictee_id: int) -> dict | None:
    rij = conn.execute("SELECT * FROM dictees WHERE id = ?", (dictee_id,)).fetchone()
    if rij is None:
        return None
    dictee = dict(rij)
    dictee["zinnen"] = json.loads(dictee["zinnen"])
    dictee["waarschuwingen"] = json.loads(dictee["waarschuwingen"])
    dictee["resultaat"] = json.loads(dictee["resultaat"]) if dictee["resultaat"] else None
    return dictee


def lijst_dictees(conn: sqlite3.Connection, week: int | None = None) -> list[dict]:
    sql = "SELECT id, week, aangemaakt_op, zinnen, resultaat FROM dictees"
    params: tuple = ()
    if week is not None:
        sql += " WHERE week = ?"
        params = (week,)
    sql += " ORDER BY id DESC"
    return [
        {
            "id": r["id"],
            "week": r["week"],
            "aangemaakt_op": r["aangemaakt_op"],
            "aantal_zinnen": len(json.loads(r["zinnen"])),
            "aantal_goed": (
                sum(z["goed"] for z in json.loads(r["resultaat"])) if r["resultaat"] else None
            ),
        }
        for r in conn.execute(sql, params).fetchall()
    ]


def verwijder_dictee(conn: sqlite3.Connection, dictee_id: int) -> bool:
    with conn:
        return conn.execute("DELETE FROM dictees WHERE id = ?", (dictee_id,)).rowcount > 0


def sla_resultaat_op(conn: sqlite3.Connection, dictee_id: int, resultaat: list[dict]) -> None:
    with conn:
        conn.execute(
            "UPDATE dictees SET resultaat = ? WHERE id = ?",
            (json.dumps(resultaat, ensure_ascii=False), dictee_id),
        )


def foutentelling(conn: sqlite3.Connection) -> dict[str, int]:
    """Hoe vaak elk woord (hanzi) fout was, over alle nagekeken dictees.

    Een foute zin zonder `foute_woorden` telt voor alle weekwoorden in die zin.
    """
    telling: dict[str, int] = {}
    for rij in conn.execute("SELECT zinnen, resultaat FROM dictees WHERE resultaat IS NOT NULL"):
        zinnen = {z["nr"]: z for z in json.loads(rij["zinnen"])}
        for res in json.loads(rij["resultaat"]):
            if res["goed"] or res["nr"] not in zinnen:
                continue
            for hanzi in res["foute_woorden"] or zinnen[res["nr"]]["woorden_van_de_week"]:
                telling[hanzi] = telling.get(hanzi, 0) + 1
    return telling
