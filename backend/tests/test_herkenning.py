import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main
from app.config import instellingen
from app.herkenning import MAX_ZIJDE, HerkendeLijst, HerkendWoord, bereid_afbeelding_voor


def maak_png(breedte=200, hoogte=100) -> bytes:
    uit = io.BytesIO()
    Image.new("RGB", (breedte, hoogte), "white").save(uit, format="PNG")
    return uit.getvalue()


class NepHerkenner:
    def __init__(self, lijst: HerkendeLijst):
        self.lijst = lijst
        self.aanroepen = []

    def herken(self, afbeelding, media_type):
        self.aanroepen.append(media_type)
        return self.lijst


LIJST = HerkendeLijst(
    week=4,
    woorden=[
        HerkendWoord(hanzi="学习", pinyin="xuéxí", betekenis="leren", betekenis_door_ai=False),
        HerkendWoord(hanzi="老师", pinyin="", betekenis="leraar", betekenis_door_ai=False),
        HerkendWoord(hanzi="朋友", pinyin="péngyou", betekenis="vriend", betekenis_door_ai=True),
        HerkendWoord(hanzi="学习", pinyin="xuéxí", betekenis="leren", betekenis_door_ai=False),
    ],
    opmerking="",
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(instellingen, "database_pad", tmp_path / "test.db")
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


def gebruik(herkenner):
    main.app.dependency_overrides[main.get_lijst_herkenner] = lambda: herkenner


def test_screenshot_uploaden(client):
    herkenner = NepHerkenner(LIJST)
    gebruik(herkenner)
    r = client.post(
        "/api/weken", files={"bestand": ("Screenshot 2026-10-02.png", maak_png(), "image/png")}
    )
    assert r.status_code == 201, r.text
    week = r.json()
    assert week["nummer"] == 4  # weeknummer van de afbeelding
    assert [w["hanzi"] for w in week["woorden"]] == ["学习", "老师", "朋友"]  # dubbel eruit
    assert week["woorden"][1]["pinyin"] == "lǎoshī"  # berekend, niet door de AI
    assert any("老师" in w and "pinyin" in w for w in week["waarschuwingen"])
    assert any("朋友" in w and "betekenis" in w for w in week["waarschuwingen"])
    assert herkenner.aanroepen == ["image/png"]


def test_screenshot_nummer_uit_formulier_wint(client):
    gebruik(NepHerkenner(LIJST))
    r = client.post(
        "/api/weken", files={"bestand": ("foto.jpg", maak_png(), "image/jpeg")}, data={"nummer": "7"}
    )
    assert r.status_code == 201 and r.json()["nummer"] == 7


def test_screenshot_bestaande_week_zonder_ai_call(client):
    herkenner = NepHerkenner(LIJST)
    gebruik(herkenner)
    client.put("/api/weken/2", json={"woorden": [{"hanzi": "你", "pinyin": "nǐ"}]})
    r = client.post(
        "/api/weken", files={"bestand": ("foto.png", maak_png(), "image/png")}, data={"nummer": "2"}
    )
    assert r.status_code == 409
    assert herkenner.aanroepen == []


def test_screenshot_zonder_weeknummer(client):
    gebruik(NepHerkenner(LIJST.model_copy(update={"week": None})))
    r = client.post("/api/weken", files={"bestand": ("foto.png", maak_png(), "image/png")})
    assert r.status_code == 422 and "weeknummer" in r.json()["detail"]


def test_screenshot_zonder_woorden(client):
    gebruik(NepHerkenner(HerkendeLijst(week=None, woorden=[], opmerking="Dit is een foto van een kat.")))
    r = client.post("/api/weken/herken", files={"bestand": ("kat.png", maak_png(), "image/png")})
    assert r.status_code == 422 and "kat" in r.json()["detail"]


def test_screenshot_zonder_api_key(client):
    gebruik(None)
    r = client.post("/api/weken", files={"bestand": ("week-01.png", maak_png(), "image/png")})
    assert r.status_code == 503
    # CSV werkt wel nog zonder key
    r = client.post(
        "/api/weken",
        files={"bestand": ("week-01.csv", "hanzi,pinyin,betekenis\n你,nǐ,jij\n".encode(), "text/csv")},
    )
    assert r.status_code == 201 and r.json()["waarschuwingen"] == []


def test_ongeldige_afbeelding(client):
    gebruik(NepHerkenner(LIJST))
    r = client.post("/api/weken/herken", files={"bestand": ("foto.png", b"geen afbeelding", "image/png")})
    assert r.status_code == 422 and "niet ondersteund" in r.json()["detail"]


def test_herkennen_en_daarna_opslaan(client):
    gebruik(NepHerkenner(LIJST))
    r = client.post("/api/weken/herken", files={"bestand": ("foto.png", maak_png(), "image/png")})
    assert r.status_code == 200
    herkend = r.json()
    assert herkend["nummer"] == 4 and len(herkend["woorden"]) == 3
    assert client.get("/api/weken").json() == []  # nog niets opgeslagen

    herkend["woorden"][0]["betekenis"] = "  leren / studeren "  # gebruiker verbetert
    r = client.put("/api/weken/4", json={"titel": "Les 4", "woorden": herkend["woorden"]})
    assert r.status_code == 200
    assert r.json()["titel"] == "Les 4"
    assert r.json()["woorden"][0]["betekenis"] == "leren / studeren"


def test_csv_herkennen_zonder_opslaan(client):
    gebruik(None)  # CSV heeft geen AI nodig
    csv = "hanzi,pinyin,betekenis\n你,nǐ,jij\n".encode()
    r = client.post("/api/weken/herken", files={"bestand": ("week-06.csv", csv, "text/csv")})
    assert r.status_code == 200
    assert r.json() == {
        "nummer": 6,
        "woorden": [{"hanzi": "你", "pinyin": "nǐ", "betekenis": "jij"}],
        "waarschuwingen": [],
    }
    assert client.get("/api/weken").json() == []


def test_put_valideert(client):
    assert client.put("/api/weken/1", json={"woorden": []}).status_code == 422
    assert client.put("/api/weken/1", json={"woorden": [{"hanzi": " ", "pinyin": "x"}]}).status_code == 422
    assert client.put("/api/weken/0", json={"woorden": [{"hanzi": "你", "pinyin": "nǐ"}]}).status_code == 422


def test_grote_afbeelding_wordt_verkleind():
    data, media_type = bereid_afbeelding_voor(maak_png(5000, 3000))
    assert media_type == "image/jpeg"
    assert max(Image.open(io.BytesIO(data)).size) == MAX_ZIJDE

    klein = maak_png()
    assert bereid_afbeelding_voor(klein) == (klein, "image/png")
