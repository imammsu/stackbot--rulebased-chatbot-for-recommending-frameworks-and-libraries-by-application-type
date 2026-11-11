# StackBot

Chatbot web tematik berbasis Flask untuk memberikan rekomendasi framework dan pustaka berdasarkan jenis aplikasi yang ingin dibuat.

StackBot menggunakan pencocokan intent berbasis aturan, tanpa machine learning, LLM, RAG, atau API eksternal.

## Fitur

- Rekomendasi untuk backend, frontend, mobile, game, desktop, data, CLI, testing, IoT, dan fullstack.
- Memahami beberapa kata tidak baku dan salah ketik ringan.
- Respons berbasis intent dengan fallback untuk pertanyaan di luar topik.
- Percakapan berkonteks dengan pilihan lanjutan.
- Riwayat percakapan dan statistik pada halaman admin.
- Antarmuka web Flask dan mode chat melalui terminal.

## Persyaratan

- Python 3.10 atau lebih baru

## Instalasi

Buat virtual environment dan aktifkan:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
venv\Scripts\activate.bat
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependency:

```bash
pip install -r requirements.txt
```

## Menjalankan aplikasi web

```bash
python app.py
```

Buka <http://127.0.0.1:5000> di browser.

Database SQLite `chatbot.db` akan dibuat otomatis saat aplikasi menerima data. File database tersebut tidak perlu di-commit ke repository.

## Mode terminal

```bash
python cli.py --tema stackbot
```

Untuk menampilkan intent dan skor klasifikasi:

```bash
python cli.py --tema stackbot --debug
```

## Pengujian

Jalankan seluruh test dengan:

```bash
pytest -v
```

## Evaluasi akurasi

Evaluasi menggunakan data pada `evaluasi/stackbot.csv`:

```bash
python evaluate.py --tema stackbot
```

Untuk membandingkan beberapa nilai ambang klasifikasi:

```bash
python evaluate.py --tema stackbot --sweep
```

## Endpoint utama

| Method | Endpoint | Keterangan |
|---|---|---|
| `GET` | `/` | Halaman utama |
| `GET` | `/chat/stackbot` | Halaman percakapan |
| `GET` | `/admin/stackbot` | Statistik dan pertanyaan yang tidak dikenali |
| `GET` | `/api/themes` | Daftar tema |
| `POST` | `/api/chat/stackbot` | Mengirim pesan chat |
| `POST` | `/api/reset/stackbot` | Menghapus konteks percakapan |

Contoh request chat:

```bash
curl -X POST http://127.0.0.1:5000/api/chat/stackbot ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"framework mobile\"}"
```

## Struktur project

```text
.
├── app.py                  # Aplikasi Flask dan endpoint API
├── cli.py                  # Chat melalui terminal
├── evaluate.py             # Evaluasi akurasi intent
├── chatbot/
│   ├── engine.py           # Preprocessing, klasifikasi, dan respons bot
│   └── storage.py          # Penyimpanan riwayat di SQLite
├── themes/                 # Konfigurasi tema dalam JSON
├── templates/              # Template HTML Jinja
├── static/                 # CSS, JavaScript, dan font
├── evaluasi/               # Dataset evaluasi
├── tests/                  # Automated tests
└── requirements.txt        # Dependency Python
```

## Konfigurasi keamanan

Untuk penggunaan selain lokal, set environment variable `SECRET_KEY` dengan nilai acak dan jangan gunakan mode debug:

PowerShell:

```powershell
$env:SECRET_KEY = "ganti-dengan-secret-yang-acak-dan-panjang"
```

Jangan menyimpan secret, file `.env`, database, atau virtual environment ke repository.
