"""
Chat lewat terminal (tanpa browser), berguna untuk mencoba pola dengan cepat.

Contoh:  python cli.py --tema stackbot --debug
"""

import argparse
from pathlib import Path

from chatbot.engine import ChatbotEngine, load_themes

FOLDER_TEMA = Path(__file__).resolve().parent / "themes"


def main() -> None:
    parser = argparse.ArgumentParser(description="Chatbot tematik di terminal")
    parser.add_argument("--tema", default="stackbot", help="id tema (nama file JSON)")
    parser.add_argument("--debug", action="store_true", help="tampilkan tag dan skor")
    args = parser.parse_args()

    themes = load_themes(FOLDER_TEMA)
    if args.tema not in themes:
        parser.error(f"tema '{args.tema}' tidak ada. Pilihan: {', '.join(themes)}")
    tema = themes[args.tema]
    engine = ChatbotEngine(tema)
    konteks = None

    print(f"{tema['bot_name']}: {tema['greeting']}")
    print("(ketik 'keluar' untuk berhenti)\n")
    while True:
        try:
            pesan = input("Kamu: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if pesan.lower() in {"keluar", "exit", "quit"}:
            break
        if not pesan:
            continue
        hasil = engine.respond(pesan, konteks)
        konteks = hasil["context"]
        print(f"\n{tema['bot_name']}: {hasil['reply']}")
        if hasil["follow_up"]:
            print(f"{tema['bot_name']}: {hasil['follow_up']}  [{' / '.join(hasil['quick_replies'])}]")
        if args.debug:
            print(f"  [tag={hasil['tag']} skor={hasil['score']}]")
        print()


if __name__ == "__main__":
    main()
