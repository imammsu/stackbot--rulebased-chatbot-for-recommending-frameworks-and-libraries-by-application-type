"""Penyimpanan riwayat percakapan di SQLite (riwayat & statistik untuk halaman admin)."""

from __future__ import annotations

import sqlite3
from contextlib import closing

SKEMA = """
CREATE TABLE IF NOT EXISTS percakapan (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tema    TEXT    NOT NULL,
    pesan   TEXT    NOT NULL,
    balasan TEXT    NOT NULL,
    tag     TEXT,               -- NULL berarti tidak dikenali (fallback)
    skor    REAL    NOT NULL,
    waktu   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_percakapan_tema ON percakapan(tema);
"""


class Storage:
    """Pembungkus tipis sqlite3. Satu koneksi per operasi agar aman dipakai Flask."""

    def __init__(self, path: str):
        self.path = path
        self._siap = False

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        if not self._siap:
            conn.executescript(SKEMA)
            self._siap = True
        return conn

    def simpan(self, tema: str, pesan: str, balasan: str, tag: str | None, skor: float) -> None:
        with closing(self._conn()) as c, c:
            c.execute(
                "INSERT INTO percakapan (tema, pesan, balasan, tag, skor) VALUES (?, ?, ?, ?, ?)",
                (tema, pesan, balasan, tag, skor),
            )

    def statistik(self, tema: str) -> dict:
        """Ringkasan untuk halaman admin."""
        with closing(self._conn()) as c:
            total = c.execute(
                "SELECT COUNT(*) FROM percakapan WHERE tema = ?", (tema,)
            ).fetchone()[0]
            dikenali = c.execute(
                "SELECT COUNT(*) FROM percakapan WHERE tema = ? AND tag IS NOT NULL", (tema,)
            ).fetchone()[0]
            per_intent = c.execute(
                """SELECT tag, COUNT(*) AS jumlah FROM percakapan
                   WHERE tema = ? AND tag IS NOT NULL
                   GROUP BY tag ORDER BY jumlah DESC""",
                (tema,),
            ).fetchall()
            tidak_dikenali = c.execute(
                """SELECT pesan, COUNT(*) AS jumlah, MAX(skor) AS skor, MAX(waktu) AS terakhir
                   FROM percakapan WHERE tema = ? AND tag IS NULL
                   GROUP BY LOWER(pesan) ORDER BY terakhir DESC LIMIT 100""",
                (tema,),
            ).fetchall()
        return {
            "total": total,
            "dikenali": dikenali,
            "tidak_dikenali_total": total - dikenali,
            "persen": round(100 * dikenali / total, 1) if total else 0.0,
            "per_intent": [dict(r) for r in per_intent],
            "tidak_dikenali": [dict(r) for r in tidak_dikenali],
        }
