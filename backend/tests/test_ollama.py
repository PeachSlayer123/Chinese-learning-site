import json
import re

import httpx
import pytest

from app import main
from app.config import instellingen
from app.dictee import AIFout, GecombineerdeBron, genereer_dictee
from app.ollama import OllamaZinnenBron, schema

from .test_api import CSV_WEEK1, CSV_WEEK2, NepBron, client, upload  # noqa: F401 (fixture)

WEEK2 = [
    {"hanzi": "学习", "pinyin": "xuéxí", "betekenis": "leren", "keer_fout": 0},
    {"hanzi": "中文", "pinyin": "zhōngwén", "betekenis": "Chinees", "keer_fout": 0},
]
WEEK1 = [
    {"hanzi": h, "pinyin": p, "betekenis": b, "keer_fout": 0}
    for h, p, b in [("我", "wǒ", "ik"), ("你", "nǐ", "jij"), ("好", "hǎo", "goed"), ("是", "shì", "zijn")]
]


class NepOllama:
    """Speelt de Ollama-server na. `wakker_na`: aantal /api/tags-checks dat hij nog slaapt."""

    def __init__(self, zinnen, wakker_na=0):
        self.zinnen = zinnen
        self.wakker_na = wakker_na
        self.chats = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            if self.wakker_na > 0:
                self.wakker_na -= 1
                raise httpx.ConnectError("slaapt", request=request)
            return httpx.Response(200, json={"models": []})
        body = json.loads(request.content)
        self.chats.append(body)
        inhoud = json.dumps({"zinnen": [{"hanzi": h, "vertaling": v} for h, v in self.zinnen]})
        return httpx.Response(200, json={"message": {"role": "assistant", "content": inhoud}})


def maak_bron(server, **k):
    wekken = []
    bron = OllamaZinnenBron(
        "http://pc:11434",
        "qwen3.5:9b",
        client=httpx.Client(transport=httpx.MockTransport(server)),
        slaap=lambda s: None,
        wek=lambda mac, bc: wekken.append(mac),
        **k,
    )
    return bron, wekken


def test_ollama_geeft_zinnen_met_tekenbeperking():
    server = NepOllama([("我学习中文。", "Ik leer Chinees.")])
    bron, wekken = maak_bron(server)
    zinnen = bron.maak_zinnen(WEEK2, WEEK1, 1)
    assert [(z.hanzi, z.bron) for z in zinnen] == [("我学习中文。", "ollama")]
    assert wekken == []
    chat = server.chats[0]
    assert chat["model"] == "qwen3.5:9b" and chat["think"] is False
    patroon = chat["format"]["properties"]["zinnen"]["items"]["properties"]["hanzi"]["pattern"]
    assert re.fullmatch(patroon, "我学习中文。")
    assert not re.fullmatch(patroon, "我很好。")  # 很 is niet gekend


def test_schema_pattern():
    p = schema("我你，。")["properties"]["zinnen"]["items"]["properties"]["hanzi"]["pattern"]
    assert p == "^[我你，。]{4,20}$"


def test_ollama_slaapt_zonder_wol_geeft_fout():
    bron, _ = maak_bron(NepOllama([], wakker_na=99))
    with pytest.raises(AIFout, match="slaapt"):
        bron.maak_zinnen(WEEK2, WEEK1, 2)


def test_ollama_wordt_gewekt():
    server = NepOllama([("你学习中文。", "Jij leert Chinees.")], wakker_na=3)
    bron, wekken = maak_bron(server, wol_mac="9C:6B:00:21:8E:AE")
    assert len(bron.maak_zinnen(WEEK2, WEEK1, 1)) == 1
    assert wekken == ["9C:6B:00:21:8E:AE"]


def test_ollama_wekken_mislukt_en_niet_opnieuw_wachten():
    server = NepOllama([], wakker_na=999)
    bron, wekken = maak_bron(server, wol_mac="9C:6B:00:21:8E:AE", wektijd=20)
    with pytest.raises(AIFout, match="20 s"):
        bron.maak_zinnen(WEEK2, WEEK1, 1)
    with pytest.raises(AIFout):
        bron.maak_zinnen(WEEK2, WEEK1, 1)
    assert len(wekken) == 1  # tweede ronde wacht niet opnieuw


def test_gecombineerd_ollama_weg_dan_claude():
    ollama, _ = maak_bron(NepOllama([], wakker_na=999))
    claude = NepBron([[("我学习中文。", "Ik leer Chinees.")]])
    zinnen, waarschuwingen = genereer_dictee(GecombineerdeBron([ollama, claude]), WEEK2, WEEK1, 1)
    assert [z["bron"] for z in zinnen] == ["ai"]
    assert any("lokale AI" in w for w in waarschuwingen)


def test_api_ollama_bron_ingesteld(client, monkeypatch):  # noqa: F811
    monkeypatch.setattr(instellingen, "zinnen_bronnen", ["ollama"])
    monkeypatch.setattr(instellingen, "ollama_url", "http://pc:11434")
    bron = main.get_zinnen_bron()
    assert [type(b).__name__ for b in bron.bronnen] == ["OllamaZinnenBron"]
    monkeypatch.setattr(instellingen, "ollama_url", "")
    monkeypatch.setattr(instellingen, "zinnen_bronnen", ["ollama", "tatoeba"])
    assert [type(b).__name__ for b in main.get_zinnen_bron().bronnen] == ["TatoebaZinnenBron"]
