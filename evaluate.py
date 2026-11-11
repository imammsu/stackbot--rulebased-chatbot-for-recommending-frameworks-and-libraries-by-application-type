"""
Evaluasi akurasi klasifikasi intent memakai file CSV (kolom: kalimat,intent).
Label `fallback` berarti kalimat di luar tema (harus tidak dikenali).

Contoh:
    python evaluate.py --tema stackbot
    python evaluate.py --tema stackbot --sweep
    python evaluate.py --tema stackbot --ambang 0.5
"""

import argparse
import csv
from pathlib import Path

from chatbot.engine import AMBANG, ChatbotEngine, load_themes

BASE_DIR = Path(__file__).resolve().parent
FOLDER_TEMA = BASE_DIR / "themes"


def muat_data(path: Path) -> list[tuple[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return [(r["kalimat"].strip(), r["intent"].strip()) for r in csv.DictReader(f)]


def evaluasi(engine: ChatbotEngine, data, ambang: float):
    """Kembalikan (akurasi, daftar_salah)."""
    engine.ambang = ambang
    salah = []
    for kalimat, label in data:
        tag, skor = engine.classify(kalimat)
        prediksi = tag or "fallback"
        if prediksi != label:
            salah.append((kalimat, label, prediksi, skor))
    benar = len(data) - len(salah)
    return benar / len(data) if data else 0.0, salah


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluasi akurasi chatbot")
    parser.add_argument("--tema", default="stackbot")
    parser.add_argument("--file", help="CSV uji (default: evaluasi/<tema>.csv)")
    parser.add_argument("--ambang", type=float, default=AMBANG)
    parser.add_argument("--sweep", action="store_true", help="bandingkan beberapa ambang")
    args = parser.parse_args()

    tema = load_themes(FOLDER_TEMA)[args.tema]
    path = Path(args.file) if args.file else BASE_DIR / "evaluasi" / f"{args.tema}.csv"
    data = muat_data(path)
    engine = ChatbotEngine(tema)
    jml_fallback = sum(1 for _, l in data if l == "fallback")
    print(f"Tema: {args.tema} | Data: {path.name} | {len(data)} kalimat ({jml_fallback} di luar tema)\n")

    if args.sweep:
        print(f"{'Ambang':>7} | {'Akurasi':>8} | Salah")
        print("-" * 28)
        for i in range(30, 75, 5):
            amb = i / 100
            akurasi, salah = evaluasi(engine, data, amb)
            tanda = "  <- default" if abs(amb - AMBANG) < 1e-9 else ""
            print(f"{amb:>7.2f} | {akurasi:>7.1%} | {len(salah)}{tanda}")
        return

    akurasi, salah = evaluasi(engine, data, args.ambang)
    print(f"Ambang {args.ambang:.2f} -> akurasi {akurasi:.1%} ({len(data) - len(salah)}/{len(data)})")
    if salah:
        print("\nKalimat yang salah:")
        for kalimat, label, prediksi, skor in salah:
            print(f"  - {kalimat!r}: harap {label}, dapat {prediksi} (skor {skor})")


if __name__ == "__main__":
    main()
