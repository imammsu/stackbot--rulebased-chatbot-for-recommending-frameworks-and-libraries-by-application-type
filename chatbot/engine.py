"""
Mesin chatbot rule-based berbasis intent.

Cara kerja (tanpa machine learning, tanpa LLM, tanpa API eksternal):
1. Praproses   : huruf kecil -> buang tanda baca -> normalisasi kata tidak baku
                 -> buang stopword.
2. Skor        : pesan dibandingkan dengan SEMUA pola di semua intent memakai
                 `similarity()` (gabungan Jaccard + difflib + cakupan).
3. Keputusan   : skor tertinggi >= AMBANG  -> respons intent tersebut,
                 selain itu                 -> salah satu respons fallback.
4. Placeholder : `{nama_bot}` diganti dengan `bot_name` milik tema.

Tugas pengembangan (intent berkonteks):
Intent boleh memiliki kunci opsional "next" berisi pertanyaan lanjutan dan
daftar opsi. Setelah intent itu dijawab, konteks disimpan (oleh pemanggil,
misalnya di Flask session). Pesan berikutnya dicocokkan lebih dulu ke opsi
konteks; bila cocok, bot memberi sub-daftar yang lebih sempit.
"""

from __future__ import annotations

import difflib
import json
import random
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------------

#: Ambang skor minimum agar pesan dianggap cocok dengan sebuah intent.
AMBANG = 0.45

#: Kunci yang wajib ada di setiap file tema. Aplikasi berhenti saat start
#: bila salah satu kunci tidak ada.
KUNCI_WAJIB_TEMA = [
    "id",
    "name",
    "bot_name",
    "avatar",
    "color",
    "description",
    "greeting",
    "suggestions",
    "fallback",
    "intents",
]

#: Bobot tiap komponen skor kemiripan (jumlahnya 1,0).
BOBOT_JACCARD = 0.4
BOBOT_DIFFLIB = 0.3
BOBOT_CAKUPAN = 0.3

#: Kamus kata tidak baku -> baku. Nilai "" berarti kata dihapus.
#: Catatan: normalisasi TIDAK berantai (satu kata dipetakan satu kali saja).
NORMALISASI = {
    # --- entri bawaan ---
    "gak": "tidak",
    "ga": "tidak",
    "nggak": "tidak",
    "enggak": "tidak",
    "tdk": "tidak",
    "gimana": "bagaimana",
    "gmn": "bagaimana",
    "yg": "yang",
    "dgn": "dengan",
    "utk": "untuk",
    "buat": "untuk",
    "sy": "saya",
    "aq": "aku",
    "gw": "gue",
    "gua": "gue",
    "lu": "kamu",
    "lo": "kamu",
    "elu": "kamu",
    "sape": "siapa",
    "ngapain": "bantu",
    "pen": "mau",
    "nyari": "",
    "cari": "",
    "kalo": "kalau",
    "klo": "kalau",
    "tp": "tapi",
    "krn": "karena",
    "dr": "dari",
    "sm": "sama",
    "bgt": "banget",
    "apk": "aplikasi",
    "ngoding": "coding",
    "thx": "thanks",
    "tq": "thanks",
    "makasi": "makasih",
    "trims": "makasih",
    # --- PRD StackBot §6.2: 15 entri baru ---
    "bikin": "",
    "bkin": "",
    "pake": "pakai",
    "app": "aplikasi",
    "hp": "mobile",
    "fe": "frontend",
    "be": "backend",
    "gim": "game",
    "rekom": "rekomendasi",
    "aja": "saja",
    "framwork": "framework",
    "frameowrk": "framework",
    "dekstop": "desktop",
    "andriod": "android",
    "frontned": "frontend",
    "fulstack": "fullstack",
    "bakedn": "backend",
    "js": "javascript",
    "ts": "typescript",
    "udah": "sudah",
    "hei": "halo",
}

#: Kata yang dibuang karena tidak membedakan intent.
STOPWORDS = {
    # --- entri bawaan ---
    "yang", "di", "ke", "dari", "dan", "atau", "untuk", "apa", "mau", "ingin",
    "pengen", "pingin", "saya", "aku", "gue", "dong", "ya", "sih", "nih", "deh",
    "kah", "itu", "ini", "ada", "dengan", "akan", "lagi", "kok", "nya", "the",
    "membuat", "tolong", "mohon", "kira", "kira2", "sebaiknya", "aja", "kalau",
    # --- PRD StackBot §6.2: 4 entri baru ---
    "pakai", "saja", "tools", "framework",
}

#: Kata umum tema yang tetap disimpan bila seluruh kata lain di kalimat adalah stopword
#: (misalnya "framework apa ya" atau "mau bikin framework" -> ["framework"]).
_FALLBACK_TOKEN = {"framework", "tools"}

#: Kosakata domain (panjang >= 5) untuk koreksi salah ketik (typo) berbasis difflib.
_KOSAKATA_BAWAAN = {
    "aplikasi", "framework", "rekomendasi", "backend", "frontend", "fullstack",
    "mobile", "android", "iphone", "lintas", "platform", "desktop", "windows",
    "komputer", "software", "program", "visualisasi", "analisis", "pengolahan",
    "grafik", "dashboard", "pustaka", "library", "command", "terminal",
    "perintah", "scripting", "testing", "pengujian", "mikrokontroler",
    "arduino", "embedded", "tampilan", "antarmuka", "website", "server",
    "teknologi", "belajar", "coding", "programming", "bingung", "makasih",
    "terima", "selamat", "fungsi", "kegunaan",
}
_KOSAKATA_AKTIF: set[str] = set(_KOSAKATA_BAWAAN) | {
    w for k in list(STOPWORDS) + list(NORMALISASI.values())
    for w in k.split() if len(w) >= 5
}

_POLA_TANDA_BACA = re.compile(r"[^\w\s]", flags=re.UNICODE)
#: Tiga atau lebih huruf identik berurutan diperkecil menjadi satu huruf
#: (contoh: "baccckend" -> "backend", "backennndddd" -> "backend", "haloooo" -> "halo").
_POLA_HURUF_BERULANG = re.compile(r"([a-z])\1{2,}")


# ---------------------------------------------------------------------------
# Praproses & skor
# ---------------------------------------------------------------------------

def _koreksi_typo(kata: str) -> str:
    """Koreksi salah ketik ringan ke kosakata domain memakai difflib (tanpa ML).

    Syarat ketat agar kata di luar tema (mis. 'presiden', 'rendang') tidak ikut berubah:
    - Panjang kata >= 5 karakter dan belum ada di kamus/kosakata.
    - Huruf pertama sama dan selisih panjang maksimal 2 karakter.
    - Rasio difflib >= 0,82 (atau >= 0,76 bila seluruh hurufnya merupakan subset target,
      seperti 'bakedn' -> 'backend' atau 'bacckend' -> 'backend').
    """
    if len(kata) < 5 or kata in _KOSAKATA_AKTIF or kata in NORMALISASI or kata in STOPWORDS:
        return kata
    terbaik, skor_terbaik = kata, 0.0
    for target in _KOSAKATA_AKTIF:
        if kata[0] != target[0] or abs(len(kata) - len(target)) > 2:
            continue
        rasio = difflib.SequenceMatcher(None, kata, target).ratio()
        ambang = 0.76 if set(kata) <= set(target) else 0.82
        if rasio >= ambang and rasio > skor_terbaik:
            terbaik, skor_terbaik = target, rasio
    return terbaik


def preprocess(teks: str) -> list[str]:
    """Ubah kalimat menjadi daftar token bersih.

    Urutan: huruf kecil -> buang tanda baca -> pangkas huruf berulang (>=3)
            -> normalisasi -> koreksi typo -> buang stopword.
    """
    teks = _POLA_TANDA_BACA.sub(" ", (teks or "").lower())
    hasil = []
    cadangan = []
    for kata in teks.split():
        kata = _POLA_HURUF_BERULANG.sub(r"\1", kata)
        kata = NORMALISASI.get(kata, kata)  # dipetakan sekali, tidak berantai
        if not kata:
            continue  # kata dihapus oleh normalisasi (contoh: "bikin")
        for bagian in kata.split():  # normalisasi bisa menghasilkan 2 kata
            bagian = _koreksi_typo(bagian)
            if bagian not in STOPWORDS:
                hasil.append(bagian)
            elif bagian in _FALLBACK_TOKEN and bagian not in cadangan:
                cadangan.append(bagian)
    return hasil if hasil else cadangan


def similarity(token_pesan: list[str], token_pola: list[str]) -> float:
    """Skor kemiripan 0..1 antara token pesan dan token pola.

    - Jaccard : irisan / gabungan himpunan kata (kemiripan isi).
    - difflib : rasio kemiripan string (tahan salah ketik ringan).
    - Cakupan : proporsi kata pola yang muncul di pesan.
    """
    if not token_pesan or not token_pola:
        return 0.0
    a, b = set(token_pesan), set(token_pola)
    irisan = len(a & b)
    jaccard = irisan / len(a | b)
    cakupan = irisan / len(b)
    rasio = difflib.SequenceMatcher(None, " ".join(token_pesan), " ".join(token_pola)).ratio()
    return BOBOT_JACCARD * jaccard + BOBOT_DIFFLIB * rasio + BOBOT_CAKUPAN * cakupan


# ---------------------------------------------------------------------------
# Validasi & pemuatan tema
# ---------------------------------------------------------------------------

def _validate_next(intent: dict, tag_valid: set[str]) -> list[str]:
    """Validasi struktur kunci opsional "next" (intent berkonteks)."""
    galat = []
    tag = intent.get("tag", "?")
    nxt = intent["next"]
    if not isinstance(nxt, dict) or not nxt.get("question"):
        return [f"intent '{tag}': 'next' harus objek dengan 'question'"]
    opsi = nxt.get("options")
    if not isinstance(opsi, list) or len(opsi) < 2:
        return [f"intent '{tag}': 'next.options' minimal 2 opsi"]
    for i, o in enumerate(opsi):
        lokasi = f"intent '{tag}' opsi #{i + 1}"
        if not o.get("label"):
            galat.append(f"{lokasi}: 'label' wajib ada")
        if not o.get("patterns"):
            galat.append(f"{lokasi}: 'patterns' wajib ada")
        for p in o.get("patterns", []):
            if not preprocess(p):
                galat.append(f"{lokasi}: pola '{p}' kosong setelah praproses")
        punya_respons, punya_goto = bool(o.get("response")), bool(o.get("goto"))
        if punya_respons == punya_goto:
            galat.append(f"{lokasi}: isi tepat salah satu dari 'response' atau 'goto'")
        if punya_goto and o["goto"] not in tag_valid:
            galat.append(f"{lokasi}: goto '{o['goto']}' tidak ada di daftar intent")
    return galat


def validate_theme(tema: dict, nama_file: str | None = None) -> list[str]:
    """Kembalikan daftar galat. Daftar kosong berarti tema valid."""
    galat = [f"kunci wajib '{k}' tidak ada" for k in KUNCI_WAJIB_TEMA if k not in tema]
    if galat:
        return galat
    if nama_file is not None and tema["id"] != nama_file:
        galat.append(f"id '{tema['id']}' harus sama dengan nama file '{nama_file}'")
    if not tema["fallback"]:
        galat.append("'fallback' minimal 1 respons")
    if not isinstance(tema["suggestions"], list):
        galat.append("'suggestions' harus list")

    tag_valid = {i.get("tag") for i in tema["intents"]}
    pemilik_pola: dict[tuple, str] = {}  # pola setelah praproses -> tag
    for intent in tema["intents"]:
        tag = intent.get("tag")
        if not tag:
            galat.append("ada intent tanpa 'tag'")
            continue
        if not intent.get("patterns"):
            galat.append(f"intent '{tag}': 'patterns' kosong")
        if not intent.get("responses"):
            galat.append(f"intent '{tag}': 'responses' kosong")
        for pola in intent.get("patterns", []):
            token = tuple(preprocess(pola))
            if not token:
                galat.append(f"intent '{tag}': pola '{pola}' kosong setelah praproses")
                continue
            pemilik = pemilik_pola.get(token)
            if pemilik and pemilik != tag:
                galat.append(
                    f"pola '{pola}' di intent '{tag}' sama dengan pola di intent '{pemilik}'"
                )
            pemilik_pola.setdefault(token, tag)
        if "next" in intent:
            galat.extend(_validate_next(intent, tag_valid))
    return galat


def load_themes(folder: str | Path) -> dict[str, dict]:
    """Muat semua `*.json` di folder tema. Lempar ValueError bila ada yang tidak valid."""
    tema_semua, semua_galat = {}, []
    for path in sorted(Path(folder).glob("*.json")):
        with open(path, encoding="utf-8") as f:
            tema = json.load(f)
        galat = validate_theme(tema, path.stem)
        if galat:
            semua_galat.extend(f"{path.name}: {g}" for g in galat)
        else:
            tema_semua[tema["id"]] = tema
    if semua_galat:
        raise ValueError("Tema tidak valid:\n  - " + "\n  - ".join(semua_galat))
    return tema_semua


# ---------------------------------------------------------------------------
# Mesin
# ---------------------------------------------------------------------------

class ChatbotEngine:
    """Mesin klasifikasi intent untuk satu tema."""

    def __init__(self, tema: dict, ambang: float = AMBANG, rng: random.Random | None = None):
        self.tema = tema
        self.ambang = ambang
        self.rng = rng or random.Random()
        self.intent_map = {i["tag"]: i for i in tema["intents"]}
        # Pola diproses sekali di awal agar setiap pesan cukup dibandingkan token.
        self._pola = [
            (intent["tag"], preprocess(p))
            for intent in tema["intents"]
            for p in intent["patterns"]
        ]

    # -- utilitas ----------------------------------------------------------
    def _isi(self, teks: str) -> str:
        """Ganti placeholder `{nama_bot}`."""
        return teks.replace("{nama_bot}", self.tema["bot_name"])

    def score_all(self, pesan: str) -> dict[str, float]:
        """Skor tertinggi per intent (berguna untuk debugging/evaluasi)."""
        token = preprocess(pesan)
        skor: dict[str, float] = {}
        for tag, pola in self._pola:
            skor[tag] = max(skor.get(tag, 0.0), similarity(token, pola))
        return skor

    # -- klasifikasi -------------------------------------------------------
    def classify(self, pesan: str) -> tuple[str | None, float]:
        """Kembalikan (tag, skor). Tag = None bila skor di bawah ambang."""
        token = preprocess(pesan)
        tag_terbaik, skor_terbaik = None, 0.0
        for tag, pola in self._pola:
            s = similarity(token, pola)
            if s > skor_terbaik:
                tag_terbaik, skor_terbaik = tag, s
        if skor_terbaik < self.ambang:
            return None, round(skor_terbaik, 3)
        return tag_terbaik, round(skor_terbaik, 3)

    def _cocokkan_opsi(self, pesan: str, konteks: str) -> tuple[dict | None, float]:
        """Cocokkan pesan dengan opsi lanjutan milik intent `konteks`."""
        intent = self.intent_map.get(konteks)
        if not intent or "next" not in intent:
            return None, 0.0
        token = preprocess(pesan)
        terbaik, skor_terbaik = None, 0.0
        for opsi in intent["next"]["options"]:
            for p in opsi["patterns"]:
                s = similarity(token, preprocess(p))
                if s > skor_terbaik:
                    terbaik, skor_terbaik = opsi, s
        if skor_terbaik < self.ambang:
            return None, round(skor_terbaik, 3)
        return terbaik, round(skor_terbaik, 3)

    # -- respons -----------------------------------------------------------
    def _jawab_intent(self, tag: str, skor: float) -> dict:
        """Bangun respons untuk intent; sertakan pertanyaan lanjutan bila ada."""
        intent = self.intent_map[tag]
        hasil = {
            "reply": self._isi(self.rng.choice(intent["responses"])),
            "tag": tag,
            "score": skor,
            "follow_up": None,
            "quick_replies": [],
            "context": None,
        }
        if "next" in intent:
            hasil["follow_up"] = self._isi(intent["next"]["question"])
            hasil["quick_replies"] = [o["label"] for o in intent["next"]["options"]]
            hasil["context"] = tag  # pemanggil menyimpan ini di sesi
        return hasil

    def respond(self, pesan: str, konteks: str | None = None) -> dict:
        """Jawab satu pesan.

        Args:
            pesan: teks dari pengguna.
            konteks: tag intent yang sedang menunggu jawaban lanjutan (atau None).

        Returns:
            dict berisi reply, tag, score, follow_up, quick_replies, dan context
            (konteks baru yang harus disimpan pemanggil; None = hapus konteks).
        """
        # 1) Konteks aktif: coba cocokkan dengan opsi lanjutan lebih dulu.
        if konteks:
            opsi, skor = self._cocokkan_opsi(pesan, konteks)
            if opsi is not None:
                if opsi.get("goto"):
                    return self._jawab_intent(opsi["goto"], skor)
                intent_induk = self.intent_map[konteks]
                opsi_lain = [
                    o["label"] for o in intent_induk["next"]["options"] if o is not opsi
                ]
                return {
                    "reply": self._isi(opsi["response"]),
                    "tag": f"{konteks}>{opsi['label']}",
                    "score": skor,
                    "follow_up": None,
                    "quick_replies": opsi_lain,
                    "context": konteks,  # tetap simpan agar pengguna bisa cek opsi saudara lainnya
                }
            # Tidak cocok: konteks dilepas, pesan diproses seperti biasa
            # (pengguna tidak "terkunci" di pertanyaan lanjutan).

        # 2) Klasifikasi normal.
        tag, skor = self.classify(pesan)
        if tag is None:
            return {
                "reply": self._isi(self.rng.choice(self.tema["fallback"])),
                "tag": None,
                "score": skor,
                "follow_up": None,
                "quick_replies": [],
                "context": None,
            }
        return self._jawab_intent(tag, skor)

    def get_response(self, pesan: str) -> str:
        """Versi sederhana tanpa konteks: hanya teks balasan."""
        hasil = self.respond(pesan)
        if hasil["follow_up"]:
            return f"{hasil['reply']}\n\n{hasil['follow_up']}"
        return hasil["reply"]
