# PRD: StackBot

**Chatbot rule-based berbasis intent untuk rekomendasi daftar framework dan pustaka**

| | |
|---|---|
| Jenis dokumen | Product Requirements Document (PRD) |
| Konteks | Tugas Praktikum Aplikasi Web, "Chatbot Tematik dengan Flask" |
| Status | Draf untuk dikerjakan |
| File tema | `themes/stackbot.json` (id: `stackbot`) |

---

## 1. Ringkasan

StackBot adalah chatbot tematik yang menjawab satu jenis pertanyaan: *"Untuk membuat aplikasi jenis X, framework atau pustaka apa saja yang tersedia?"*. Pengguna cukup menyebut jenis aplikasinya (backend, frontend, fullstack, mobile, game, desktop, data, CLI, testing, atau IoT). Bot membalas **daftar pilihan beserta bahasa pemrogramannya**, tanpa peringkat dan tanpa klaim "terbaik".

Bot dibangun di atas kerangka praktikum (Flask, `engine.py` berbasis skor kemiripan, tema dalam satu file JSON). Pekerjaan utama tugas ini adalah **basis pengetahuan** (`stackbot.json`), pengujian, evaluasi, dan satu tugas pengembangan.

## 2. Batasan dan ketentuan tugas

### 2.1 Batasan dari dosen dan pemberi tugas

| Ketentuan | Penerapan di StackBot |
|---|---|
| Rule-based, berbasis intent | Pencocokan pola ke intent lewat `similarity()` (Jaccard + difflib + cakupan). Tidak ada proses belajar |
| Tematik | Satu domain: rekomendasi framework dan pustaka per jenis aplikasi. Di luar itu → fallback |
| Bukan machine learning / LLM | Tidak ada model, embedding, atau klasifikasi ML |
| Tanpa RAG | Seluruh pengetahuan ada di `stackbot.json`, tanpa pencarian dokumen atau vector database |
| Tanpa API lain | Tidak ada panggilan ke layanan eksternal. Semua berjalan lokal |
| Framework web | Flask |

### 2.2 Ketentuan dari modul praktikum

| # | Tugas wajib | Cara dipenuhi |
|---|---|---|
| 1 | Tema baru: ≥ 10 intent, tiap intent ≥ 5 pola dan ≥ 2 respons, 4 saran | 14 intent, pola minimum 8 per intent, respons minimum 2, 4 saran |
| 1 | Pola diambil dari wawancara ≥ 5 calon pengguna | **Belum dikerjakan** (lihat bagian 9) |
| 2 | ≥ 8 kasus uji tema baru di `tests/test_engine.py`, semua lolos | Lihat bagian 8.1 |
| 3 | ≥ 10 kata tidak baku di `NORMALISASI` | 15 entri baru, lihat bagian 6.2 |
| 4 | `evaluasi/stackbot.csv` ≥ 20 kalimat (termasuk 4 di luar tema), uji coba 3 teman, laporan akurasi sebelum dan sesudah perbaikan | Lihat bagian 8.3 |
| 5 | Satu tugas pengembangan | Intent berkonteks (bagian 10) |
| 6 | Kumpul: ZIP tanpa `venv/` dan `*.db`, laporan PDF maks. 5 halaman | Bagian 11 |

## 3. Tujuan dan non-tujuan

**Tujuan**
1. Bot menjawab dengan benar pertanyaan "mau bikin X pakai apa" untuk 10 jenis aplikasi.
2. Setiap daftar bersumber dari dokumentasi resmi, dan bot menyatakan bahwa itu *daftar pilihan, bukan peringkat*.
3. Pertanyaan di luar tema ditolak sopan dengan fallback yang mengarahkan ke topik yang bisa dijawab.
4. Akurasi pada data uji ≥ 90% pada ambang 0,45 (mengikuti uji akurasi di modul).

**Non-tujuan**
- Membandingkan framework (contoh: "Flask vs Django"), memberi peringkat, atau menyebut "terbaik".
- Menjelaskan cara memakai framework, memberi tutorial, atau menulis kode.
- Menyebut harga, nomor versi, atau angka performa.
- Menjawab berdasarkan bahasa pemrograman yang dikuasai pengguna (diputuskan tidak dipakai, karena tidak semua bahasa bisa dipakai di semua platform).

## 4. Pengguna dan skenario

**Pengguna utama:** mahasiswa atau pemula yang baru mulai memilih teknologi untuk proyek atau tugas dan belum tahu opsi apa yang ada.

| ID | Sebagai... | Saya ingin... | Agar... |
|---|---|---|---|
| US-1 | Mahasiswa | menyebut jenis aplikasi dan langsung dapat daftar framework | tahu pilihan yang tersedia |
| US-2 | Pemula yang bingung | disuruh menyebut jenis aplikasi bila pertanyaanku terlalu umum | bisa mengarahkan pertanyaan |
| US-3 | Pengguna | bot tetap paham kalimat gaul atau salah ketik ("bikin app hp pake apa") | tidak perlu menulis baku |
| US-4 | Pengguna | bot menolak dengan sopan pertanyaan di luar topik dan memberi contoh | tahu apa yang bisa ditanyakan |
| US-5 | Pengguna | tombol saran untuk pertanyaan populer | cepat memulai |

## 5. Kebutuhan fungsional

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-1 | Bot mengenali 14 intent (tabel 5.1) dengan skor kemiripan ≥ ambang 0,45 | Wajib |
| FR-2 | Bila skor tertinggi < 0,45, bot memberi salah satu dari 3 fallback | Wajib |
| FR-3 | Setiap respons rekomendasi diakhiri sumber ("Sumber: dokumentasi resmi") dan kalimat "bukan peringkat" | Wajib |
| FR-4 | Respons `{nama_bot}` diganti otomatis dengan nama bot | Wajib |
| FR-5 | 4 tombol saran di halaman chat: *Framework backend, Framework fullstack, Framework mobile, Framework game* | Wajib |
| FR-6 | Pesan kosong dan > 500 karakter ditolak dengan kode 400 (sudah ditangani aplikasi) | Wajib |
| FR-7 | Halaman admin menampilkan pertanyaan yang tidak dikenali untuk dijadikan pola baru | Wajib |
| FR-8 | Intent berkonteks: bot bertanya lanjutan dan mengingat konteks di sesi | Tugas pengembangan |

### 5.1 Daftar intent

| # | Intent | Fungsi | Jumlah pola | Jumlah respons |
|---|---|---|---|---|
| 1 | `salam` | Sapaan | 17 | 3 |
| 2 | `identitas` | Siapa bot dan fungsinya | 10 | 2 |
| 3 | `terima_kasih` | Terima kasih dan pamit | 17 | 2 |
| 4 | `rekom_backend` | Daftar framework backend | 10 | 2 |
| 5 | `rekom_frontend` | Daftar framework frontend | 9 | 2 |
| 6 | `rekom_mobile` | Daftar framework mobile | 10 | 2 |
| 7 | `rekom_game` | Daftar engine dan framework game | 10 | 2 |
| 8 | `rekom_desktop` | Daftar framework desktop | 9 | 2 |
| 9 | `rekom_data` | Daftar pustaka data dan visualisasi | 9 | 2 |
| 10 | `rekom_cli` | Daftar pustaka CLI | 8 | 2 |
| 11 | `rekom_testing` | Daftar framework testing | 9 | 2 |
| 12 | `rekom_iot` | Daftar framework IoT dan embedded | 10 | 2 |
| 13 | `rekom_fullstack` | Daftar framework fullstack | 10 | 2 |
| 14 | `kategori_belum_disebut` | Pertanyaan terlalu umum → bot bertanya jenis aplikasi | 17 | 2 |

Isi lengkap ada di `stackbot.json`.

### 5.2 Pola respons

- **Intent rekomendasi:** dua versi respons. Versi 1 dikelompokkan per kategori sub-jenis (misalnya native, lintas platform), versi 2 dikelompokkan per bahasa. Keduanya menyebut bahwa ini daftar pilihan dan mencantumkan sumber.
- **`kategori_belum_disebut`:** tidak memberi daftar. Bot bertanya balik jenis aplikasi yang dimaksud.

## 6. Kebutuhan data

### 6.1 Skema file tema

Sesuai `KUNCI_WAJIB_TEMA` di `engine.py`. Aplikasi berhenti saat start bila ada yang salah.

| Kunci | Isi di StackBot |
|---|---|
| `id` | `stackbot` (harus sama dengan nama file) |
| `name` | Rekomendasi Framework dan Pustaka |
| `bot_name` | StackBot |
| `avatar` | 🧰 |
| `color` | `#0f766e` |
| `description` | Satu kalimat tentang cakupan bot |
| `greeting` | Sapaan awal yang menyebut 10 jenis aplikasi |
| `suggestions` | 4 saran (lihat FR-5) |
| `fallback` | 3 respons |
| `intents` | 14 objek `{tag, patterns, responses}` |

### 6.2 Perubahan yang wajib di `chatbot/engine.py`

Mesin bawaan modul belum cocok untuk tema ini karena kata-kata yang muncul di hampir semua pola ("bikin", "pakai", "framework", "tools") membuat skor antar-intent berdekatan. Tambahkan ke kamus berikut.

**`NORMALISASI`** (15 entri baru, memenuhi syarat ≥ 10):

```python
"bikin": "", "bkin": "", "pake": "pakai", "app": "aplikasi", "hp": "mobile",
"fe": "frontend", "be": "backend", "gim": "game", "rekom": "rekomendasi",
"aja": "saja", "framwork": "framework", "js": "javascript", "ts": "typescript",
"udah": "sudah", "hei": "halo",
```

**`STOPWORDS`** (4 entri baru):

```python
"pakai", "saja", "tools", "framework",
```

Catatan: mesin tidak merantai normalisasi (satu kata dipetakan sekali), jadi `"bikin": ""` langsung menghapus kata itu.

### 6.3 Aturan penulisan pola yang harus dijaga

1. **Pola yang sama (setelah praproses) tidak boleh ada di dua intent**, karena `validate_theme()` menolaknya dan aplikasi tidak mau jalan.
2. **Hindari pola satu kata umum.** Pola `siapa` pernah membuat "siapa presiden indonesia" salah dijawab sebagai `identitas` (skor 0,54), jadi pola identitas ditulis minimal dua kata bermakna.
3. **Pola tidak boleh kosong setelah praproses** (semua katanya stopword).
4. Tulis pola dari kalimat asli pengguna, bukan dari tebakan.
5. Pola pendek untuk tombol saran ("framework backend") sengaja ada, karena setelah `framework` jadi stopword klik tombol itu menjadi satu kata kunci.

## 7. Arsitektur

Mengikuti kerangka praktikum, tidak ada komponen baru.

```
Browser (chat.js, fetch)  ->  Flask app.py  ->  ChatbotEngine  ->  themes/stackbot.json
                                   |
                                   +-> SQLite (riwayat, statistik)
```

```
aplikasi-final/
├── app.py
├── cli.py
├── evaluate.py
├── chatbot/engine.py        # <- tambah NORMALISASI dan STOPWORDS (6.2)
├── themes/stackbot.json     # <- file baru
├── evaluasi/stackbot.csv    # <- file baru
├── templates/ static/
└── tests/test_engine.py     # <- tambah >= 8 uji
```

**Alur satu pesan:** praproses (huruf kecil → buang tanda baca → normalisasi → buang stopword) → hitung skor ke semua pola → ambil tertinggi → skor ≥ 0,45 ? respons intent : fallback → isi placeholder → simpan ke SQLite.

## 8. Rencana pengujian dan evaluasi

### 8.1 Uji tema (≥ 8 kasus, ditambahkan ke `tests/test_engine.py`)

Kasus berikut sudah dijalankan terhadap engine yang dipatch di bagian 6.2 dan lolos.

| # | Kalimat | Intent yang diharapkan |
|---|---|---|
| 1 | `halo` | `salam` |
| 2 | `kamu siapa` | `identitas` |
| 3 | `mau bikin backend pakai apa` | `rekom_backend` |
| 4 | `bikin app android pakai apa` | `rekom_mobile` |
| 5 | `bikin gim 2d pake apa` | `rekom_game` |
| 6 | `pemrograman esp32` | `rekom_iot` |
| 7 | `frontend dan backend sekaligus pakai apa` | `rekom_fullstack` |
| 8 | `mau bikin website` | `kategori_belum_disebut` |
| 9 | `Framework fullstack` (teks tombol saran) | `rekom_fullstack` |
| 10 | `siapa presiden indonesia` | fallback (`None`) |

Contoh bentuk kode:

```python
@pytest.mark.parametrize("pesan, intent", [
    ("halo", "salam"),
    ("mau bikin backend pakai apa", "rekom_backend"),
    # ...
])
def test_klasifikasi_stackbot(pesan, intent):
    engine = ChatbotEngine(THEMES["stackbot"])
    tag, _ = engine.classify(pesan)
    assert tag == intent
```

### 8.2 Uji bawaan yang akan rusak

Menambah tema membuat dua uji bawaan gagal. Ubah:

- `test_api_themes`: `assert len(data) == 3` → `== 4`.
- `test_semua_tema_termuat`: tambahkan `"stackbot"` ke himpunan yang dicek.

### 8.3 Evaluasi akurasi

- Buat `evaluasi/stackbot.csv` (kolom `kalimat,intent`), minimal 20 baris, **minimal 4 berlabel `fallback`** (di luar tema).
- Kalimat uji **tidak boleh sama dengan pola** di JSON, dan sebaiknya ditulis oleh orang lain.
- Jalankan `python evaluate.py --tema stackbot` dan `--sweep` untuk membandingkan ambang.
- Ajak 3 teman mencoba bot, lalu salin pertanyaan yang tidak dikenali dari `/admin/stackbot` menjadi pola baru.
- Laporkan akurasi **sebelum** dan **sesudah** perbaikan beserta alasannya.

**Hasil awal (uji mandiri oleh penulis):** pada 68 kalimat yang saya susun, mesin bawaan modul mencapai 94,1% dan engine yang dipatch (bagian 6.2) mencapai 100% pada ambang 0,35 sampai 0,60 (97,1% pada 0,70). **Angka ini optimistis** karena kalimatnya ditulis oleh orang yang sudah tahu isi pola. Pakai angka dari data teman sebagai angka laporan.

## 9. Pekerjaan yang masih harus kamu lakukan

| Prioritas | Pekerjaan | Alasan |
|---|---|---|
| 1 | Wawancarai ≥ 5 calon pengguna dan tambahkan pola dari kalimat asli mereka | Syarat tugas no. 1. Pola saat ini berasal dari knowledge mapping, bukan wawancara |
| 2 | Verifikasi setiap nama teknologi ke dokumentasi resminya dan catat sumbernya | Rubrik "jawaban akurat" (25%) |
| 3 | Patch `engine.py` (6.2) | Tanpa ini akurasi turun dan beberapa kalimat gaul gagal |
| 4 | Buat `evaluasi/stackbot.csv` dan uji ke 3 teman | Syarat tugas no. 4 |
| 5 | Tulis uji, jalankan `pytest -v` | Syarat tugas no. 2 |
| 6 | Kerjakan tugas pengembangan | Bobot 20% |

## 10. Tugas pengembangan

Dari enam opsi di modul, disaring dengan batasan tugasmu (tanpa ML, LLM, dan API lain):

| Opsi | Boleh? | Catatan |
|---|---|---|
| **Intent berkonteks** | **Dipilih** | Murni aturan, cocok dengan tema |
| Grafik di admin | Boleh | Aman, tapi kurang terkait tema |
| Mode gelap dan aksesibilitas | Boleh | Aman |
| Stemming (Sastrawi) | Dengan hati-hati | Berbasis aturan, tapi pustaka tambahan |
| Pencocokan TF-IDF | **Hindari** | Memakai scikit-learn, mudah dianggap ML |
| LLM sebagai fallback | **Dilarang** | Melanggar ketentuan tugas |

**Rancangan intent berkonteks:** tambahkan kunci `"next"` pada intent tertentu. Bot bertanya lanjutan dan menyimpan konteks di sesi, lalu jawaban pengguna dipetakan ke pilihan yang lebih sempit.

| Setelah intent | Pertanyaan lanjutan | Jawaban dipetakan ke |
|---|---|---|
| `rekom_mobile` | "Target Android, iOS, atau keduanya?" | Sub-daftar native Android, native iOS, lintas platform |
| `rekom_game` | "2D atau 3D?" | Sub-daftar sesuai dimensi |
| `rekom_data` | "Untuk pengolahan atau visualisasi?" | Sub-daftar pengolahan atau visualisasi |
| `kategori_belum_disebut` | "Jenis aplikasi apa?" | Intent kategori yang disebut |

Fitur ini juga membantu mengurangi masalah respons yang terlalu panjang (bagian 12).

## 11. Pengumpulan

- Folder proyek dalam satu ZIP, **tanpa `venv/` dan `*.db`**.
- Laporan PDF maksimal 5 halaman: tangkapan layar, hasil `pytest -v`, hasil `evaluate.py`, tabel perbaikan, dan jawaban seluruh pertanyaan pemahaman di modul.

### Pemetaan rubrik

| Aspek | Bobot | Yang menentukan nilai |
|---|---|---|
| Aplikasi berjalan | 15% | `python app.py` tanpa galat. JSON harus lolos `validate_theme` |
| Basis pengetahuan | 25% | ≥ 10 intent, pola bervariasi dan realistis, **jawaban akurat dan sopan** |
| Pengujian | 15% | ≥ 8 uji tema baru, semua lolos |
| Evaluasi dan perbaikan | 15% | Akurasi sebelum dan sesudah, dengan alasan |
| Tugas pengembangan | 20% | Fitur berfungsi, kode rapi dan berkomentar |
| Laporan | 10% | Lengkap, jelas, pertanyaan pemahaman terjawab |

## 12. Risiko dan mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| **Daftar framework usang atau salah** | Menurunkan nilai akurasi | Verifikasi tiap nama, catat sumber di laporan, tulis "daftar pilihan, bukan peringkat" |
| **Respons terlalu panjang** (20 sampai 25 nama pada desktop, game, testing, data) | Modul menyebut "jawaban panjang berisi banyak topik" sebagai hal yang dihindari. Gelembung chat sulit dibaca | Pangkas ke 6 sampai 10 pilihan utama, atau pakai sub-daftar lewat intent berkonteks |
| **Kategori beririsan** (Next.js, Nuxt, Astro, AdonisJS, Remix muncul di backend, frontend, dan fullstack) | Terlihat tidak konsisten | Jelaskan di laporan bahwa irisan ini memang fakta, bukan kesalahan |
| **Kata umum membuat skor berdekatan** | Salah intent | Patch `engine.py` (6.2), uji pasangan kalimat mirip |
| **Pola dari knowledge mapping, bukan pengguna nyata** | Pola kurang realistis | Wawancara 5 orang dan tambah pola dari `/admin` |
| **Pola kategori_belum_disebut mirip pola kategori lain** ("mau bikin website" vs "bikin aplikasi web") | Intent tertukar | Uji kalimat perbatasan di evaluasi |

### Daftar nama yang perlu dicek statusnya

Ini berdasarkan ingatan saya saat menyusun, **bukan hasil pengecekan**. Cek di situs resmi masing-masing sebelum dikumpulkan.

| Nama | Di intent | Yang perlu dicek |
|---|---|---|
| Xamarin | `rekom_mobile` | Apakah dukungan resminya sudah berakhir |
| PhoneGap | `rekom_mobile` | Apakah produknya masih ada (Apache Cordova berbeda) |
| Mbed OS | `rekom_iot` | Apakah ada pengumuman akhir masa dukungan |
| Remix | `rekom_frontend`, `rekom_fullstack` | Apakah arahnya sudah bergeser ke React Router |
| Pigpio | `rekom_iot` | Pustaka GPIO Raspberry Pi, bukan mikrokontroler. Cek kecocokan kategori dan dukungannya |
| Three.js | `rekom_game` | Menyebut dirinya pustaka grafis 3D, bukan engine game |
| Slint, DuckDB, Apache Arrow | `rekom_desktop`, `rekom_data` | Daftar bahasa pendukung sering bertambah |

## 13. Perubahan dari knowledge mapping awal

Isi daftar framework **tidak diubah**. Yang diperbaiki hanya hal teknis agar JSON valid dan akurasi mesin terjaga.

| Perubahan | Alasan |
|---|---|
| Tombol saran ke-4 diganti "Framework game" | Versi awal menulis "Framework mobile" dua kali |
| Semua respons memakai `{nama_bot}` | Konsisten dan otomatis diganti mesin |
| Kutip tak berpasangan diganti kutip tunggal tipografis (‘ ’) | Menjaga JSON valid |
| Pola `rekom_cli` yang terpotong dan janggal diperbaiki | "framework untuk program baris" dan "cli pakai apa perintah" |
| Pola ganda "bikin tool terminal" dihapus | Duplikat setelah praproses |
| Pola identitas diubah: `ini siapa`, `ini bot apa`, `bot ini untuk apa`, `bisa bantu apa` | Menjadi satu kata setelah praproses sehingga menangkap pertanyaan di luar tema |
| Ditambah pola "framework backend/frontend/mobile/game/fullstack/desktop/data/cli/testing" | Agar klik tombol saran selalu dikenali |
| ".NET MAUI", "urfave/cli", "lintas bahasa" dirapikan | Salah ketik di draf |
| "Sumber" ganda dan "serta C (Pigpio)" yang redundan dihapus | Duplikat |

## 14. Definition of Done

- [ ] `python app.py` jalan tanpa galat dan `/chat/stackbot` terbuka.
- [ ] `validate_theme()` mengembalikan daftar kosong.
- [ ] `pytest -v` lolos semua, termasuk ≥ 8 uji tema baru.
- [ ] `evaluasi/stackbot.csv` ≥ 20 baris (≥ 4 di luar tema), akurasi ≥ 90%.
- [ ] Pola ditambah dari wawancara ≥ 5 orang dan uji coba 3 teman.
- [ ] Semua nama teknologi sudah diverifikasi dan sumbernya dicatat.
- [ ] Tugas pengembangan berfungsi dan kodenya berkomentar.
- [ ] ZIP (tanpa `venv/` dan `*.db`) dan laporan PDF ≤ 5 halaman siap.
