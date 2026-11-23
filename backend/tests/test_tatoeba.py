import gzip
import random

import pytest

from app import main
from app.config import instellingen
from app.dictee import AIFout, GecombineerdeBron, RuweZin, genereer_dictee
from app.tatoeba import TatoebaZinnenBron, laad

from .test_api import CSV_WEEK1, CSV_WEEK2, NepBron, client, upload  # noqa: F401 (fixture)

ZINNEN = [
    ("1", "我学习中文。", "Ik leer Chinees.", "I study Chinese."),
    ("2", "你学习中文吗？", "", "Do you study Chinese?"),  # 吗 is onbekend → valt weg
    ("3", "你好！", "Hallo!", "Hello!"),  # geen weekwoord van week 2
    ("4", "你是我。", "Jij bent mij.", ""),  # week 1-woorden, geen weekwoord van week 2
    ("5", "我是中文。", "", "I am Chinese."),
    ("6", "中文", "Chinees", "Chinese"),  # te kort
]
WEEK2 = [
    {"hanzi": "学习", "pinyin": "xuéxí", "betekenis": "leren", "keer_fout": 0},
    {"hanzi": "中文", "pinyin": "zhōngwén", "betekenis": "Chinees", "keer_fout": 0},
]
WEEK1 = [
    {"hanzi": h, "pinyin": p, "betekenis": b, "keer_fout": 0}
    for h, p, b in [("我", "wǒ", "ik"), ("你", "nǐ", "jij"), ("好", "hǎo", "goed"), ("是", "shì", "zijn")]
]


@pytest.fixture
def tatoeba_bestand(tmp_path):
    pad = tmp_path / "tatoeba.tsv.gz"
    with gzip.open(pad, "wt", encoding="utf-8", newline="") as f:
        f.write("id\thanzi\tnl\ten\n")
        for rij in ZINNEN:
            f.write("\t".join(rij) + "\n")
    laad.cache_clear()
    return pad


def test_tatoeba_kiest_alleen_zinnen_binnen_woordenschat(tatoeba_bestand):
    bron = TatoebaZinnenBron(tatoeba_bestand, rng=random.Random(1))
    zinnen = bron.maak_zinnen(WEEK2, WEEK1, aantal=5)
    assert {z.hanzi for z in zinnen} == {"我学习中文。", "我是中文。"}
    assert all(z.bron == "tatoeba" for z in zinnen)
    vertalingen = {z.hanzi: z.vertaling for z in zinnen}
    assert vertalingen["我学习中文。"] == "Ik leer Chinees."
    assert vertalingen["我是中文。"] == "I am Chinese. (EN)"  # geen NL → Engels, gemarkeerd


def test_tatoeba_dekt_eerst_alle_weekwoorden(tatoeba_bestand):
    bron = TatoebaZinnenBron(tatoeba_bestand, rng=random.Random(2))
    zinnen = bron.maak_zinnen(WEEK2, WEEK1, aantal=1)
    assert zinnen[0].hanzi == "我学习中文。"  # bevat beide weekwoorden


def test_tatoeba_zonder_bestand_geeft_niets(tmp_path):
    laad.cache_clear()
    assert TatoebaZinnenBron(tmp_path / "bestaat-niet.gz").maak_zinnen(WEEK2, WEEK1, 3) == []


def test_gecombineerd_ai_vult_enkel_aan(tatoeba_bestand):
    ai = NepBron([[("你学习。", "Jij leert."), ("我学习中文。", "dubbel")]])
    bron = GecombineerdeBron([TatoebaZinnenBron(tatoeba_bestand, rng=random.Random(3)), ai])
    zinnen, waarschuwingen = genereer_dictee(bron, WEEK2, WEEK1, aantal=3)
    assert [z["bron"] for z in zinnen] == ["tatoeba", "tatoeba", "ai"]
    assert zinnen[0]["bron_url"].startswith("https://tatoeba.org/")
    assert zinnen[2]["hanzi"] == "你学习。" and zinnen[2]["bron_url"] is None
    assert ai.aanroepen[0]["aantal"] == 1  # alleen wat Tatoeba niet had
    assert waarschuwingen == []


def test_gecombineerd_ai_fout_na_tatoeba_geeft_waarschuwing(tatoeba_bestand):
    class KapotteAI:
        def maak_zinnen(self, *a, **k):
            raise AIFout("Geen verbinding met de AI.")

    bron = GecombineerdeBron([TatoebaZinnenBron(tatoeba_bestand), KapotteAI()])
    zinnen, waarschuwingen = genereer_dictee(bron, WEEK2, WEEK1, aantal=4)
    assert len(zinnen) == 2
    assert any("AI kon niet aanvullen" in w for w in waarschuwingen)


def test_gecombineerd_ai_fout_zonder_tatoeba_zinnen_blijft_fout():
    class KapotteAI:
        def maak_zinnen(self, *a, **k):
            raise AIFout("kapot")

    with pytest.raises(AIFout):
        GecombineerdeBron([KapotteAI()]).maak_zinnen(WEEK2, WEEK1, 2)


def test_api_dictee_uit_tatoeba_zonder_api_key(client, monkeypatch, tatoeba_bestand):  # noqa: F811
    monkeypatch.setattr(instellingen, "anthropic_api_key", "")
    monkeypatch.setattr(instellingen, "tatoeba_pad", tatoeba_bestand)
    upload(client, "week-01.csv", CSV_WEEK1)
    upload(client, "week-02.csv", CSV_WEEK2)
    r = client.post("/api/dictees", json={"week": 2, "aantal_zinnen": 2})
    assert r.status_code == 201, r.text
    zinnen = r.json()["zinnen"]
    assert {z["bron"] for z in zinnen} == {"tatoeba"}
    assert {z["hanzi"] for z in zinnen} == {"我学习中文。", "我是中文。"}


def test_api_week1_uit_tatoeba_en_503_als_alleen_claude_zonder_key(client, monkeypatch, tatoeba_bestand):  # noqa: F811
    monkeypatch.setattr(instellingen, "anthropic_api_key", "")
    monkeypatch.setattr(instellingen, "tatoeba_pad", tatoeba_bestand)
    upload(client, "week-01.csv", CSV_WEEK1)  # Tatoeba heeft 你是我。
    r = client.post("/api/dictees", json={"week": 1, "aantal_zinnen": 1})
    assert r.status_code == 201
    monkeypatch.setattr(instellingen, "zinnen_bronnen", ["claude"])
    assert client.post("/api/dictees", json={"week": 1}).status_code == 503


def test_ruwe_zin_standaard_bron_is_ai():
    assert RuweZin(hanzi="你好。", vertaling="Hallo.").bron == "ai"
