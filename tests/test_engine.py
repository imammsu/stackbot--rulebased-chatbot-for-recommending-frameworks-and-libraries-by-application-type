"""
Pengujian mesin chatbot dan aplikasi Flask.

Jalankan:  pytest -v
"""

import copy
import json
import random
from pathlib import Path

import pytest

from app import THEMES, create_app
from chatbot.engine import (
    AMBANG,
    NORMALISASI,
    ChatbotEngine,
    preprocess,
    similarity,
    validate_theme,
)
from evaluate import evaluasi, muat_data

FOLDER_TEMA = Path(__file__).resolve().parent.parent / "themes"
FILE_EVALUASI = Path(__file__).resolve().parent.parent / "evaluasi" / "stackbot.csv"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return ChatbotEngine(THEMES["stackbot"], rng=random.Random(0))


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=tmp_path / "uji.db")
    app.config["TESTING"] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# Praproses & skor
# ---------------------------------------------------------------------------

def test_preprocess_huruf_kecil_dan_tanda_baca():
    assert preprocess("Halo, Bot!!") == ["halo", "bot"]


def test_preprocess_normalisasi_dan_stopword():
    # bikin -> dihapus, app -> aplikasi, hp -> mobile, pake -> pakai (stopword), apa (stopword)
    assert preprocess("bikin app hp pake apa") == ["aplikasi", "mobile"]


def test_normalisasi_minimal_10_entri_baru_prd():
    entri_baru = ["bikin", "bkin", "pake", "app", "hp", "fe", "be", "gim", "rekom",
                  "aja", "framwork", "js", "ts", "udah", "hei"]
    assert all(k in NORMALISASI for k in entri_baru)
    assert len(entri_baru) >= 10


def test_similarity_identik_dan_kosong():
    assert similarity(["game", "2d"], ["game", "2d"]) == pytest.approx(1.0)
    assert similarity([], ["game"]) == 0.0


# ---------------------------------------------------------------------------
# Tema
# ---------------------------------------------------------------------------

def test_semua_tema_termuat():
    assert set(THEMES) == {"stackbot"}


def test_validate_theme_stackbot_tanpa_galat():
    with open(FOLDER_TEMA / "stackbot.json", encoding="utf-8") as f:
        assert validate_theme(json.load(f), "stackbot") == []


def test_tema_memenuhi_syarat_modul():
    tema = THEMES["stackbot"]
    assert len(tema["intents"]) >= 10
    assert len(tema["suggestions"]) == 4
    for intent in tema["intents"]:
        assert len(intent["patterns"]) >= 5, intent["tag"]
        assert len(intent["responses"]) >= 2, intent["tag"]


def test_respons_rekomendasi_memuat_sumber_dan_bukan_peringkat():
    """FR-3: setiap respons rekomendasi (termasuk sub-daftar) memuat sumber & 'bukan peringkat'."""
    for intent in THEMES["stackbot"]["intents"]:
        if not intent["tag"].startswith("rekom_"):
            continue
        teks = list(intent["responses"])
        teks += [o["response"] for o in intent.get("next", {}).get("options", []) if "response" in o]
        for t in teks:
            assert "Sumber: dokumentasi resmi" in t, intent["tag"]
            assert "bukan peringkat" in t, intent["tag"]


def test_validate_menolak_kunci_hilang():
    tema = copy.deepcopy(THEMES["stackbot"])
    del tema["avatar"]
    assert any("avatar" in g for g in validate_theme(tema, "stackbot"))


def test_validate_menolak_pola_duplikat_lintas_intent():
    tema = copy.deepcopy(THEMES["stackbot"])
    tema["intents"][0]["patterns"].append("framework backend")  # milik rekom_backend
    assert any("sama dengan pola" in g for g in validate_theme(tema, "stackbot"))


def test_validate_menolak_id_beda_dengan_nama_file():
    assert any("nama file" in g for g in validate_theme(THEMES["stackbot"], "lain"))


# ---------------------------------------------------------------------------
# Klasifikasi tema StackBot (PRD §8.1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pesan, intent", [
    ("halo", "salam"),
    ("kamu siapa", "identitas"),
    ("mau bikin backend pakai apa", "rekom_backend"),
    ("bikin app android pakai apa", "rekom_mobile"),
    ("bikin gim 2d pake apa", "rekom_game"),
    ("pemrograman esp32", "rekom_iot"),
    ("frontend dan backend sekaligus pakai apa", "rekom_fullstack"),
    ("mau bikin website", "kategori_belum_disebut"),
    ("Framework fullstack", "rekom_fullstack"),
    ("siapa presiden indonesia", None),
    # tambahan
    ("bikin app hp pake apa", "rekom_mobile"),
    ("makasih ya", "terima_kasih"),
    ("Framework game", "rekom_game"),
    ("Framework mobile", "rekom_mobile"),
    ("Framework backend", "rekom_backend"),
    ("mau bikin framework", "kategori_belum_disebut"),
    ("saya mau nyari framework", "kategori_belum_disebut"),
    ("framework apa ya", "kategori_belum_disebut"),
    ("frameowrk apa ya", "kategori_belum_disebut"),
    ("framework aplikasi", "kategori_belum_disebut"),
    ("mau bikin aplikasi", "kategori_belum_disebut"),
    ("FRAMEWORK BACCCKEND", "rekom_backend"),
    ("FRAMEWORK BACKENNNDDDD", "rekom_backend"),
    ("FRAMEWORK BACCKENNNDDD", "rekom_backend"),
    ("framework bakedn", "rekom_backend"),
    ("cara masak nasi goreng", None),
])
def test_klasifikasi_stackbot(engine, pesan, intent):
    tag, skor = engine.classify(pesan)
    assert tag == intent, f"{pesan!r} -> {tag} (skor {skor})"
    if intent is None:
        assert skor < AMBANG


def test_placeholder_nama_bot_diganti(engine):
    for _ in range(10):
        balasan = engine.respond("halo")["reply"]
        assert "{nama_bot}" not in balasan
        assert "StackBot" in balasan


def test_fallback_berasal_dari_tema(engine):
    hasil = engine.respond("siapa presiden indonesia")
    assert hasil["tag"] is None
    assert hasil["reply"] in THEMES["stackbot"]["fallback"]


# ---------------------------------------------------------------------------
# Tugas pengembangan: intent berkonteks
# ---------------------------------------------------------------------------

def test_konteks_mobile_4_jalur(engine):
    pertama = engine.respond("framework mobile")
    assert pertama["context"] == "rekom_mobile"
    assert pertama["quick_replies"] == ["Android", "iOS", "Cross Platform", "Hybrid"]
    kedua = engine.respond("android", konteks=pertama["context"])
    assert kedua["tag"] == "rekom_mobile>Android"
    assert "Jetpack Compose" in kedua["reply"]
    assert "SwiftUI" not in kedua["reply"]
    assert kedua["context"] == "rekom_mobile"
    assert kedua["quick_replies"] == ["iOS", "Cross Platform", "Hybrid"]
    ketiga = engine.respond("Hybrid", konteks=kedua["context"])
    assert ketiga["tag"] == "rekom_mobile>Hybrid"
    assert "Capacitor" in ketiga["reply"]


def test_konteks_game_3d_lalu_pindah_2d(engine):
    r1 = engine.respond("3d", konteks="rekom_game")
    assert r1["tag"] == "rekom_game>3D"
    assert "Unreal Engine" in r1["reply"]
    assert r1["context"] == "rekom_game"
    assert r1["quick_replies"] == ["2D"]
    r2 = engine.respond("kalau 2d", konteks=r1["context"])
    assert r2["tag"] == "rekom_game>2D"
    assert "Phaser" in r2["reply"]


def test_konteks_data_3_jalur(engine):
    assert engine.respond("buat grafik", konteks="rekom_data")["tag"] == "rekom_data>Visualisasi"
    assert engine.respond("dashboard", konteks="rekom_data")["tag"] == "rekom_data>Dashboard"


def test_konteks_desktop_testing_iot(engine):
    assert engine.respond("Berbasis Web", konteks="rekom_desktop")["tag"] == "rekom_desktop>Berbasis Web"
    assert engine.respond("Native Windows", konteks="rekom_desktop")["tag"] == "rekom_desktop>Native Windows"
    assert engine.respond("Unit Test", konteks="rekom_testing")["tag"] == "rekom_testing>Unit Test"
    assert engine.respond("E2E & Browser", konteks="rekom_testing")["tag"] == "rekom_testing>E2E & Browser"
    assert engine.respond("RTOS", konteks="rekom_iot")["tag"] == "rekom_iot>RTOS"
    assert engine.respond("Raspberry Pi", konteks="rekom_iot")["tag"] == "rekom_iot>Raspberry Pi"


def test_konteks_kategori_diarahkan_ke_intent(engine):
    pertama = engine.respond("mau bikin website")
    assert pertama["context"] == "kategori_belum_disebut"
    assert pertama["follow_up"]
    kedua = engine.respond("mobile", konteks=pertama["context"])
    assert kedua["tag"] == "rekom_mobile"
    assert kedua["context"] == "rekom_mobile"  # berantai: lanjut tanya jalur mobile


def test_konteks_dilepas_bila_jawaban_tidak_cocok(engine):
    hasil = engine.respond("framework backend", konteks="rekom_mobile")
    assert hasil["tag"] == "rekom_backend"
    assert hasil["context"] is None


# ---------------------------------------------------------------------------
# Aplikasi Flask
# ---------------------------------------------------------------------------

def test_halaman_utama_dan_chat(client):
    assert client.get("/").status_code == 200
    res = client.get("/chat/stackbot")
    assert res.status_code == 200
    assert "StackBot" in res.get_data(as_text=True)


def test_tema_tidak_ada_404(client):
    assert client.get("/chat/tidakada").status_code == 404
    assert client.post("/api/chat/tidakada", json={"message": "halo"}).status_code == 404


def test_api_themes(client):
    data = client.get("/api/themes").get_json()
    assert len(data) == 1
    assert data[0]["id"] == "stackbot"


def test_api_chat_berhasil(client):
    data = client.post("/api/chat/stackbot", json={"message": "halo"}).get_json()
    assert data["tag"] == "salam"
    assert "StackBot" in data["reply"]


@pytest.mark.parametrize("pesan", ["", "   ", "a" * 501])
def test_api_chat_tolak_400(client, pesan):
    assert client.post("/api/chat/stackbot", json={"message": pesan}).status_code == 400


def test_api_chat_konteks_tersimpan_di_sesi(client):
    r1 = client.post("/api/chat/stackbot", json={"message": "framework game"}).get_json()
    assert r1["quick_replies"] == ["2D", "3D"]
    r2 = client.post("/api/chat/stackbot", json={"message": "2D"}).get_json()
    assert r2["tag"] == "rekom_game>2D"


def test_api_reset_menghapus_konteks(client):
    client.post("/api/chat/stackbot", json={"message": "framework game"})
    client.post("/api/reset/stackbot")
    r = client.post("/api/chat/stackbot", json={"message": "2D"}).get_json()
    assert r["tag"] != "rekom_game>2D"


def test_admin_menampilkan_pertanyaan_tidak_dikenali(client):
    client.post("/api/chat/stackbot", json={"message": "siapa presiden indonesia"})
    html = client.get("/admin/stackbot").get_data(as_text=True)
    assert "siapa presiden indonesia" in html


# ---------------------------------------------------------------------------
# Evaluasi CSV (PRD §8.3)
# ---------------------------------------------------------------------------

def test_evaluasi_csv_memenuhi_syarat_dan_akurasi(engine):
    data = muat_data(FILE_EVALUASI)
    assert len(data) >= 20
    assert sum(1 for _, label in data if label == "fallback") >= 4

    semua_pola = {
        p.strip().lower()
        for intent in THEMES["stackbot"]["intents"]
        for p in intent["patterns"]
    }
    for kalimat, _ in data:
        assert kalimat.lower() not in semua_pola, f"Kalimat uji sama dengan pola: {kalimat}"

    akurasi, salah = evaluasi(engine, data, AMBANG)
    assert akurasi >= 0.90, f"Akurasi {akurasi:.1%}, salah: {salah}"

