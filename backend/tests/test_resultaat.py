import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import db, main
from app.config import instellingen
from tests.test_api import CSV_WEEK1, CSV_WEEK2, NepBron, upload

ZINNEN = [("我学习中文。", "Ik leer Chinees."), ("你学习中文。", "Jij leert Chinees.")]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(instellingen, "database_pad", tmp_path / "test.db")
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


@pytest.fixture
def dictee(client):
    """Week 1 + 2 en een dictee van week 2 met twee zinnen."""
    upload(client, "week-01.csv", CSV_WEEK1)
    upload(client, "week-02.csv", CSV_WEEK2)
    main.app.dependency_overrides[main.get_zinnen_bron] = lambda: NepBron([ZINNEN])
    return client.post("/api/dictees", json={"week": 2, "aantal_zinnen": 2}).json()


def keer_fout(client) -> dict[str, int]:
    return {w["hanzi"]: w["keer_fout"] for w in client.get("/api/woorden").json()}


def test_nieuw_dictee_heeft_nog_geen_resultaat(client, dictee):
    assert dictee["resultaat"] is None
    assert client.get("/api/dictees").json()[0]["aantal_goed"] is None


def test_resultaat_opslaan(client, dictee):
    r = client.put(
        f"/api/dictees/{dictee['id']}/resultaat",
        json={"zinnen": [{"nr": 2, "goed": False, "foute_woorden": ["中文"]}, {"nr": 1, "goed": True}]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["resultaat"] == [
        {"nr": 1, "goed": True, "foute_woorden": []},
        {"nr": 2, "goed": False, "foute_woorden": ["中文"]},
    ]
    assert client.get(f"/api/dictees/{dictee['id']}").json()["resultaat"] == r.json()["resultaat"]
    assert client.get("/api/dictees").json()[0]["aantal_goed"] == 1

    fouten = keer_fout(client)
    assert fouten["中文"] == 1 and fouten["学习"] == 0 and fouten["你"] == 0


def test_foute_zin_zonder_woorden_telt_voor_alle_weekwoorden(client, dictee):
    client.put(f"/api/dictees/{dictee['id']}/resultaat", json={"zinnen": [{"nr": 1, "goed": False}]})
    fouten = keer_fout(client)
    assert fouten["学习"] == 1 and fouten["中文"] == 1
    assert fouten["我"] == 0  # geen weekwoord


def test_resultaat_opnieuw_sturen_overschrijft(client, dictee):
    url = f"/api/dictees/{dictee['id']}/resultaat"
    client.put(url, json={"zinnen": [{"nr": 1, "goed": False}]})
    client.put(url, json={"zinnen": [{"nr": 1, "goed": True}]})
    assert keer_fout(client)["学习"] == 0


def test_zin_met_foute_woorden_is_fout(client, dictee):
    r = client.put(
        f"/api/dictees/{dictee['id']}/resultaat",
        json={"zinnen": [{"nr": 1, "goed": True, "foute_woorden": ["学习", "学习"]}]},
    )
    assert r.json()["resultaat"] == [{"nr": 1, "goed": False, "foute_woorden": ["学习"]}]


@pytest.mark.parametrize(
    "zinnen",
    [
        [],  # leeg
        [{"nr": 9, "goed": True}],  # onbekende zin
        [{"nr": 1, "goed": True}, {"nr": 1, "goed": False}],  # dubbel
        [{"nr": 1, "goed": False, "foute_woorden": ["朋友"]}],  # woord staat niet in de zin
    ],
)
def test_resultaat_valideert(client, dictee, zinnen):
    r = client.put(f"/api/dictees/{dictee['id']}/resultaat", json={"zinnen": zinnen})
    assert r.status_code == 422


def test_resultaat_onbestaand_dictee(client):
    assert client.put("/api/dictees/99/resultaat", json={"zinnen": [{"nr": 1, "goed": True}]}).status_code == 404


def test_vaak_foute_woorden_gaan_mee_in_de_prompt(client, dictee):
    client.put(
        f"/api/dictees/{dictee['id']}/resultaat",
        json={"zinnen": [{"nr": 1, "goed": False, "foute_woorden": ["中文"]}]},
    )
    bron = NepBron([ZINNEN])
    main.app.dependency_overrides[main.get_zinnen_bron] = lambda: bron
    client.post("/api/dictees", json={"week": 2, "aantal_zinnen": 1})
    assert "中文 (1x fout)" in bron.aanroepen[0]["opmerking"]


def test_week_vervangen_bewaart_dictees(client, dictee):
    r = upload(client, "week-02.csv", CSV_WEEK2, vervang="true", titel="Nieuw")
    assert r.status_code == 201 and r.json()["titel"] == "Nieuw"
    assert client.get(f"/api/dictees/{dictee['id']}").status_code == 200


def test_oude_database_krijgt_resultaat_kolom(tmp_path):
    pad = tmp_path / "oud.db"
    conn = sqlite3.connect(pad)
    conn.executescript(
        """
        CREATE TABLE dictees (id INTEGER PRIMARY KEY AUTOINCREMENT, week INTEGER NOT NULL,
            aangemaakt_op TEXT NOT NULL, zinnen TEXT NOT NULL, waarschuwingen TEXT NOT NULL);
        INSERT INTO dictees (week, aangemaakt_op, zinnen, waarschuwingen) VALUES (1, 'x', '[]', '[]');
        """
    )
    conn.commit()
    conn.close()

    db.initialiseer(pad)
    conn = db.verbind(pad)
    assert db.haal_dictee(conn, 1)["resultaat"] is None
    conn.close()
