# Chat, Landing & Admin Page Overrides — StackBot (Modern Minimalist SaaS Refactor)

> **Overrides `design-system/stackbot/MASTER.md`** menggunakan kombinasi skill **`ui-styling`** (shadcn/ui *New York* + Tailwind token discipline) dan **`ui-ux-pro-max`** (Modern Minimalist SaaS + Evolved Soft UI / Glassmorphism).

## 1. Palet & Atmosfer Visual (Modern Minimalist SaaS)

- **Ambient Canvas & Grid Texture:** Latar belakang menggunakan radial spotlight halus di bagian atas (`rgba(20, 184, 166, 0.16)` di mode gelap / `0.09` di mode terang) yang dipadukan dengan grid geometris tipis `32px × 32px`.
- **Elevasi Multi-lapis (shadcn *New York*):** Kartu permukaan (`--color-card`) menggunakan border `1px` presisi dengan *inner top highlight* (`inset 0 1px 0 rgba(255,255,255,0.05)`) pada mode gelap dan bayangan lembut berlapis pada mode terang.

| Token | Dark Mode (Default) | Light Mode (Toggle) | Kontras WCAG AA |
|-------|---------------------|---------------------|-----------------|
| `--color-background` | `#070B12` | `#F8FAFC` | — |
| `--color-surface` | `#0C121E` | `#F1F5F9` | — |
| `--color-card` | `#101827` | `#FFFFFF` | — |
| `--color-foreground` | `#F8FAFC` | `#0F172A` | > 15:1 |
| `--color-muted-foreground` | `#94A3B8` | `#475569` | ≥ 5.5:1 |
| `--color-accent` | `#14B8A6` (Teal 500) | `#0F766E` (Teal 700) | 7.8:1 (dark) / 5.5:1 (light) |
| `--color-on-accent` | `#042F2E` | `#FFFFFF` | ≥ 5.5:1 |

## 2. Komponen Utama (Tanpa Mengubah Struktur/Alur Fungsi)

1. **Split SaaS Landing (`templates/index.html`):**
   - Tata letak 2 kolom (*Hero Value Proposition* + *Interactive Theme Bento Card*) dengan *eyebrow live pill*, *capability pills* (`14 Intent Terkurasi`, `10 Kategori Aplikasi`, `Intent Berkonteks`, `Toleransi Typo`), serta badge domain teknologi.
2. **Bento Recommendation Cards (`templates/chat.html` & `static/css/style.css`):**
   - Setiap kelompok kategori di dalam `.bubble--rich` dirender sebagai blok kartu `.group` terpisah dengan label monospace `.group__label` di kiri dan chip `.tag` di kanan.
   - Setiap `.tag` memisahkan nama teknologi (`.tag__name`) dan badge bahasa pemrograman berwarna aksen lembut (`.tag__lang`).
3. **Floating Command Composer Dock (`.composer__dock`):**
   - Panel input mengambang bergaya *command palette* dengan `backdrop-filter: blur(16px)`, chip saran di bagian atas, kotak teks berfokus cincin cahaya (`focus-within`), serta indikator tombol `<kbd>Enter</kbd>` dan `<kbd>Shift</kbd>+<kbd>Enter</kbd>`.
4. **SaaS Analytics Admin (`templates/admin.html`):**
   - Kartu KPI (`.stat`) dilengkapi garis aksen gradien atas, ikon indikator, angka utama monospace, dan sub-keterangan metrik.
