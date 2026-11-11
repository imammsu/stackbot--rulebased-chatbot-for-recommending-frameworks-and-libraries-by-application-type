"""
Aplikasi web chatbot tematik (Flask).

Jalankan:  python app.py   lalu buka http://127.0.0.1:5000
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, session

from chatbot.engine import ChatbotEngine, load_themes
from chatbot.storage import Storage

BASE_DIR = Path(__file__).resolve().parent
FOLDER_TEMA = BASE_DIR / "themes"
MAKS_PANJANG_PESAN = 500

# Tema dimuat & divalidasi saat start. Bila ada tema tidak valid, aplikasi berhenti.
try:
    THEMES = load_themes(FOLDER_TEMA)
except ValueError as err:  # pragma: no cover - dijalankan saat start
    print(err, file=sys.stderr)
    sys.exit(1)


def create_app(db_path: str | os.PathLike | None = None) -> Flask:
    """Pabrik aplikasi. `db_path` bisa diganti saat pengujian."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-stackbot-ganti-di-produksi")
    app.config["JSON_AS_ASCII"] = False

    storage = Storage(str(db_path or BASE_DIR / "chatbot.db"))
    engines = {tid: ChatbotEngine(t) for tid, t in THEMES.items()}

    def ambil_tema(tema_id: str) -> dict:
        tema = THEMES.get(tema_id)
        if tema is None:
            abort(404)
        return tema

    # -- konteks percakapan (tugas pengembangan: intent berkonteks) ----------
    def baca_konteks(tema_id: str) -> str | None:
        return session.get("konteks", {}).get(tema_id)

    def tulis_konteks(tema_id: str, nilai: str | None) -> None:
        konteks = dict(session.get("konteks", {}))
        if nilai:
            konteks[tema_id] = nilai
        else:
            konteks.pop(tema_id, None)
        session["konteks"] = konteks

    # -- halaman -------------------------------------------------------------
    @app.get("/")
    def index():
        return render_template("index.html", themes=list(THEMES.values()))

    @app.get("/chat/<tema_id>")
    def chat(tema_id):
        tema = ambil_tema(tema_id)
        tulis_konteks(tema_id, None)  # halaman baru = percakapan baru
        return render_template("chat.html", tema=tema, maks=MAKS_PANJANG_PESAN)

    @app.get("/admin/<tema_id>")
    def admin(tema_id):
        tema = ambil_tema(tema_id)
        return render_template("admin.html", tema=tema, stat=storage.statistik(tema_id))

    # -- API -----------------------------------------------------------------
    @app.get("/api/themes")
    def api_themes():
        return jsonify([
            {k: t[k] for k in ("id", "name", "bot_name", "avatar", "color", "description")}
            for t in THEMES.values()
        ])

    @app.post("/api/chat/<tema_id>")
    def api_chat(tema_id):
        ambil_tema(tema_id)
        data = request.get_json(silent=True) or {}
        pesan = str(data.get("message", "")).strip()
        if not pesan:
            return jsonify(error="Pesan tidak boleh kosong."), 400
        if len(pesan) > MAKS_PANJANG_PESAN:
            return jsonify(error=f"Pesan maksimal {MAKS_PANJANG_PESAN} karakter."), 400

        hasil = engines[tema_id].respond(pesan, baca_konteks(tema_id))
        tulis_konteks(tema_id, hasil["context"])

        balasan_lengkap = hasil["reply"]
        if hasil["follow_up"]:
            balasan_lengkap += "\n\n" + hasil["follow_up"]
        storage.simpan(tema_id, pesan, balasan_lengkap, hasil["tag"], hasil["score"])

        return jsonify(
            reply=hasil["reply"],
            follow_up=hasil["follow_up"],
            quick_replies=hasil["quick_replies"],
            tag=hasil["tag"],
            score=hasil["score"],
        )

    @app.post("/api/reset/<tema_id>")
    def api_reset(tema_id):
        ambil_tema(tema_id)
        tulis_konteks(tema_id, None)
        return jsonify(ok=True)

    @app.errorhandler(404)
    def tidak_ditemukan(_err):
        if request.path.startswith("/api/"):
            return jsonify(error="Tidak ditemukan."), 404
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
