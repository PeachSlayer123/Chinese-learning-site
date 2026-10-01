import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import instellingen
from app.dictee import RuweZin

CSV_WEEK1 = "hanzi,pinyin,betekenis\n我,wǒ,ik\n你,nǐ,jij\n好,hǎo,goed\n是,shì,zijn\n".encode()
CSV_WEEK2 = "﻿hanzi;pinyin;betekenis\n学习;xuéxí;leren\n中文;zhōngwén;Chinees\n".encode()


class NepBron:
    """Speelt Claude na: geeft vaste zinnen terug, en houdt bij hoe vaak hij gevraagd werd."""

    def __init__(self, rondes: list[list[tuple[str, str]]]):
        self.rondes = rondes
        self.aanroepen = []

    def maak_zinnen(self, weekwoorden, bekende_woorden, aantal, opmerking=""):
        self.aanroepen.append({"aantal": aantal, "opmerking": opmerking})
        ronde = self.rondes[min(len(self.aanroepen) - 1, len(self.rondes) - 1)]
        return [RuweZin(hanzi=h, vertaling=v) for h, v in ronde][:aantal]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(instellingen, "database_pad", tmp_path / "test.db")
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


def upload(client, naam, inhoud, **velden):
    return client.post("/api/weken", files={"bestand": (naam, inhoud, "text/csv")}, data=velden)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_en_opvragen(client):
    r = upload(client, "week-01.csv", CSV_WEEK1, titel="Begin")
    assert r.status_code == 201
    week = r.json()
    assert week["nummer"] == 1 and week["titel"] == "Begin" and week["aantal_woorden"] == 4
    assert week["woorden"][0] == {
        "id": 1, "hanzi": "我", "pinyin": "wǒ", "betekenis": "ik", "week": 1, "keer_fout": 0
    }

    # puntkomma + BOM (Excel) en nummer via formulier
    r = upload(client, "lijst.csv", CSV_WEEK2, nummer="2")
    assert r.status_code == 201 and r.json()["aantal_woorden"] == 2

    assert [w["nummer"] for w in client.get("/api/weken").json()] == [1, 2]
    assert len(client.get("/api/woorden").json()) == 6
    assert len(client.get("/api/woorden", params={"tot_week": 1}).json()) == 4
    assert client.get("/api/weken/2").json()["woorden"][0]["hanzi"] == "学习"
    assert client.get("/api/weken/9").status_code == 404


def test_upload_bestaat_al_en_vervangen(client):
    upload(client, "week-01.csv", CSV_WEEK1)
    assert upload(client, "week-01.csv", CSV_WEEK1).status_code == 409
    r = upload(client, "week-01.csv", CSV_WEEK2, vervang="true")
    assert r.status_code == 201 and r.json()["aantal_woorden"] == 2


def test_upload_fouten(client):
    assert upload(client, "lijst.csv", CSV_WEEK1).status_code == 422  # geen weeknummer
    r = upload(client, "week-01.csv", "hanzi,betekenis\n你,jij\n".encode())
    assert r.status_code == 422 and "pinyin" in r.json()["detail"]


def test_week_verwijderen(client):
    upload(client, "week-01.csv", CSV_WEEK1)
    assert client.delete("/api/weken/1").status_code == 204
    assert client.get("/api/weken").json() == []
    assert client.get("/api/woorden").json() == []
    assert client.delete("/api/weken/1").status_code == 404


def test_dictee_genereren(client):
    upload(client, "week-01.csv", CSV_WEEK1)
    upload(client, "week-02.csv", CSV_WEEK2)
    bron = NepBron([[("我学习中文。", "Ik leer Chinees."), ("你好！", "Hallo!")]])
    main.app.dependency_overrides[main.get_zinnen_bron] = lambda: bron

    r = client.post("/api/dictees", json={"week": 2, "aantal_zinnen": 1})
    assert r.status_code == 201, r.text
    dictee = r.json()
    zin = dictee["zinnen"][0]
    assert zin["hanzi"] == "我学习中文。"
    assert zin["pinyin"] == "Wǒ xuéxí zhōngwén."
    assert zin["woorden_van_de_week"] == ["学习", "中文"]
    assert zin["onbekende_tekens"] == []
    assert dictee["waarschuwingen"] == []

    assert client.get(f"/api/dictees/{dictee['id']}").json() == dictee
    assert client.get("/api/dictees", params={"week": 2}).json()[0]["aantal_zinnen"] == 1
    assert client.delete(f"/api/dictees/{dictee['id']}").status_code == 204


def test_dictee_vraagt_nieuwe_zin_bij_afkeuring(client):
    upload(client, "week-01.csv", CSV_WEEK1)
    upload(client, "week-02.csv", CSV_WEEK2)
    bron = NepBron(
        [
            [("我学习中文。", "Ik leer Chinees."), ("你好！", "Hallo!")],  # 2e zin: geen weekwoord
            [("你学习中文。", "Jij leert Chinees.")],
        ]
    )
    main.app.dependency_overrides[main.get_zinnen_bron] = lambda: bron

    r = client.post("/api/dictees", json={"week": 2, "aantal_zinnen": 2})
    assert r.status_code == 201
    assert [z["hanzi"] for z in r.json()["zinnen"]] == ["我学习中文。", "你学习中文。"]
    assert len(bron.aanroepen) == 2
    assert bron.aanroepen[1]["aantal"] == 1
    assert "你好！" in bron.aanroepen[1]["opmerking"]


def test_dictee_met_onbekende_tekens_geeft_waarschuwing(client):
    upload(client, "week-01.csv", CSV_WEEK1)
    bron = NepBron([[("我很好。", "Het gaat goed met mij.")]])
    main.app.dependency_overrides[main.get_zinnen_bron] = lambda: bron

    r = client.post("/api/dictees", json={"week": 1, "aantal_zinnen": 1})
    assert r.status_code == 201
    zin = r.json()["zinnen"][0]
    assert zin["onbekende_tekens"] == ["很"]
    assert zin["pinyin"] == "Wǒ hěn hǎo."
    assert any("很" in w for w in r.json()["waarschuwingen"])
    assert len(bron.aanroepen) == 3  # 1 + 2 extra rondes geprobeerd


def test_dictee_zonder_api_key(client, monkeypatch):
    monkeypatch.setattr(instellingen, "anthropic_api_key", "")
    upload(client, "week-01.csv", CSV_WEEK1)
    assert client.get("/api/health").json()["ai_beschikbaar"] is False
    assert client.post("/api/dictees", json={"week": 1}).status_code == 503


def test_dictee_onbestaande_week(client):
    main.app.dependency_overrides[main.get_zinnen_bron] = lambda: NepBron([[]])
    assert client.post("/api/dictees", json={"week": 7}).status_code == 404
