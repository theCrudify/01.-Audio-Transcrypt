# Local AI Transcription Studio

Aplikasi web untuk mengubah rekaman audio/video menjadi teks **sepenuhnya di komputer sendiri**, tanpa cloud. Memakai [whisper.cpp](https://github.com/ggerganov/whisper.cpp) dengan akselerasi GPU Vulkan, berjalan di **Windows dan Linux**, dan bisa dipakai sendiri di laptop maupun bersama satu kelompok belajar lewat jaringan lokal.

## Mulai cepat

Cukup clone lalu jalankan **satu script**. Pada run pertama, semua yang dibutuhkan diunduh dan diinstall otomatis: Python (Windows), paket sistem (Linux), whisper.cpp dengan GPU Vulkan, library Python, dan model AI. Setelah itu server aplikasi langsung berjalan dan siap dipakai lewat browser.

**Linux (Debian/Ubuntu)**

```bash
git clone https://github.com/theCrudify/01.-Audio-Transcrypt.git
cd 01.-Audio-Transcrypt
bash scripts/start_app.sh
```

**Windows 10/11**

Clone repository ini, atau di GitHub pilih *Code → Download ZIP* lalu ekstrak. Setelah itu double-click `scripts\start_app.bat`.

**Lalu** buka http://127.0.0.1:8000, tunggu badge **Siap**, dan upload file. Hentikan server dengan `Ctrl+C`.

| | Linux | Windows |
|---|---|---|
| Yang perlu dilakukan pengguna | Ketik password `sudo` sekali, jika ada paket sistem yang belum terpasang | Klik **Yes** di prompt administrator, jika *Microsoft Visual C++ Redistributable* belum terpasang. Jika muncul *Windows protected your PC*, klik **More info → Run anyway** |
| Run pertama | ±4 menit, unduhan ±650 MB | Beberapa menit, unduhan ±650 MB |
| Run berikutnya | Langsung start, tanpa internet | Sama |
| Status pengujian | Sudah dites dari folder kosong sampai siap pakai | Semua unduhan sudah dicek bisa diakses tanpa login, tetapi alur lengkapnya **belum dites di PC Windows asli**. Jika ada kendala, buka [issue](https://github.com/theCrudify/01.-Audio-Transcrypt/issues) beserta pesan `[setup]`-nya |

Detail apa saja yang disiapkan ada di [Instalasi](#instalasi). Jika ada yang gagal, lihat [Troubleshooting](#troubleshooting).

## Daftar isi

1. [Fitur](#fitur)
2. [Instalasi](#instalasi)
3. [Menggunakan aplikasi](#menggunakan-aplikasi)
4. [Mode server (dipakai bersama)](#mode-server-dipakai-bersama)
5. [GPU yang didukung](#gpu-yang-didukung)
6. [Model & kualitas transkripsi](#model--kualitas-transkripsi)
7. [Bedakan pembicara (speaker diarization)](#bedakan-pembicara-speaker-diarization)
8. [Konfigurasi (environment variable)](#konfigurasi-environment-variable)
9. [API](#api)
10. [Struktur project](#struktur-project)
11. [Cakupan & batasan](#cakupan--batasan)
12. [Lisensi, privasi & atribusi](#lisensi-privasi--atribusi)
13. [Troubleshooting](#troubleshooting)
14. [Untuk maintainer: binary whisper Windows](#untuk-maintainer-binary-whisper-windows)

## Fitur

- Upload audio/video lewat browser: `aac, flac, m4a, mkv, mov, mp3, mp4, ogg, opus, wav, webm`, tanpa batas ukuran (bisa dibatasi dengan `MAX_UPLOAD_MB`).
- Rekam langsung dari mikrofon.
- Fokus bahasa **Indonesia & Inggris**, termasuk bahasa Indonesia yang bercampur istilah Inggris. ±100 bahasa lain tersedia lewat pencarian, atau pakai deteksi otomatis.
- Peringatan jika bahasa yang dipilih tidak cocok dengan isi rekaman.
- Transkripsi dalam bahasa asli, atau terjemahan langsung ke bahasa Inggris.
- Bedakan pembicara (*Pembicara 1, 2, …*), tanpa login atau token.
- Timestamp per baris (klik untuk memutar bagian itu); salin, atau unduh sebagai TXT / SRT.
- Ekstrak audio dari video menjadi WAV.
- GPU Vulkan (AMD, NVIDIA, Intel); jika GPU gagal, otomatis pindah ke CPU.
- Melewati bagian hening (VAD) agar tidak muncul teks "halusinasi".
- Tampilan ID/EN, responsif (HP, tablet, laptop), tema terang/gelap.
- Setelah setup, berjalan offline. Tidak butuh Anaconda maupun FFmpeg.

## Instalasi

### Prasyarat

Satu-satunya syarat: **internet saat run pertama**. Prasyarat berikut diinstall otomatis oleh launcher jika belum ada, dari sumber resminya:

| | Windows (`start_app.bat`) | Linux Debian/Ubuntu (`start_app.sh`) |
|---|---|---|
| Python 3.10+ | Python 3.12 dari python.org lewat `winget` (per pengguna, tanpa admin). Python yang sudah ada (python.org, Anaconda, `py`) langsung dipakai. | `python3` bawaan; `python3-venv` lewat `apt` |
| Tool build whisper.cpp | Tidak perlu: whisper.cpp diunduh siap pakai | `git build-essential cmake libvulkan-dev glslc mesa-vulkan-drivers` lewat `apt` (minta password `sudo`) |
| Microsoft Visual C++ Redistributable x64 | Installer resmi dari Microsoft (minta izin administrator) | Tidak perlu |

**Tidak** diinstall otomatis: driver GPU. Driver bawaan Windows/Linux biasanya sudah cukup; tanpa driver Vulkan aplikasi tetap jalan di CPU, hanya lebih lambat.

Install manual hanya perlu jika otomatisnya gagal, misalnya Windows tanpa `winget` (unduh Python dari [python.org](https://www.python.org/downloads/), centang *Add python.exe to PATH*) atau Linux selain Debian/Ubuntu (install padanan paket di atas lewat package manager distro).

### Yang disiapkan otomatis

`scripts/start_app.sh` (Linux) dan `scripts\start_app.bat` (Windows) menjalankan `python -m app.bootstrap` sebelum server start. Script ini menyiapkan:

| File / folder | Ukuran | Sumber | Fungsi |
|---|---|---|---|
| `.venv/` | ±270 MB | PyPI (`requirements/base.txt`) | Library Python. Diinstall ulang otomatis jika `requirements/base.txt` berubah |
| `build-vulkan/` (Windows) | 18 MB | [GitHub Release project ini](https://github.com/theCrudify/01.-Audio-Transcrypt/releases/tag/whisper-vulkan-bd9985c) | whisper.cpp siap pakai dengan GPU Vulkan. Jika rilis ini tidak tersedia, dipakai [whisper.cpp resmi](https://github.com/ggml-org/whisper.cpp/releases) versi CPU (9 MB, lebih lambat) dan setup mencoba versi GPU lagi di run berikutnya |
| `build-linux/` (Linux) | – | Source [whisper.cpp-amd](https://github.com/lemonade-sdk/whisper.cpp-amd) commit `bd9985c` | whisper.cpp di-build di komputer itu (beberapa menit) |
| `models/ggml-large-v3-turbo-q5_0.bin` | 574 MB | Hugging Face `ggerganov/whisper.cpp` | Model transkripsi |
| `models/ggml-silero-v5.1.2.bin` | 0,9 MB | Hugging Face `ggml-org/whisper-vad` | Model VAD (melewati hening) |
| `models/pyannote-segmentation-3.0.onnx` | 6 MB | GitHub Release `k2-fsa/sherpa-onnx` | Bedakan pembicara: memotong giliran bicara |
| `models/3dspeaker_speech_eres2net_sv_en_voxceleb_16k.onnx` | 27 MB | GitHub Release `k2-fsa/sherpa-onnx` | Bedakan pembicara: mengenali suara |

- **Tidak perlu mengunduh apa pun secara manual**, dan tidak perlu login ke Hugging Face atau situs lain.
- **Hanya sekali.** File yang sudah ada dilewati, jadi run berikutnya langsung start.
- **Aman dari unduhan rusak.** Setiap file dicek sha256-nya. Unduhan yang terputus dibuang; jalankan ulang script untuk mengunduh lagi dari awal.
- **Komputer tanpa internet:** salin folder `models/` (dan `.venv/` atau `build-*/` dari OS yang sama) dari komputer lain.
- Jika `WHISPER_CLI` atau `WHISPER_MODEL_PATH` diisi, bagian itu tidak disiapkan.

Contoh output run pertama di Linux:

```text
[setup] Membuat virtual environment .venv ...
[setup] Menginstall dependensi Python ...
[setup] Mengambil source whisper.cpp ...
[setup] Build whisper.cpp dengan Vulkan (sekali saja, beberapa menit) ...
[setup] Mengunduh ggml-large-v3-turbo-q5_0.bin ...
        100%  574 / 574 MB
[setup] Mengunduh ggml-silero-v5.1.2.bin ...
[setup] Semua file siap.
...
Starting app on http://127.0.0.1:8000
```

Setup bisa juga dijalankan tanpa start server: `python3 -m app.bootstrap` (Windows: `python -m app.bootstrap`).

### Cek setup & test

Launcher sudah menjalankan pengecekan ini otomatis. Untuk menjalankannya manual:

```bash
.venv/bin/python -m app.verify              # Windows: .venv\Scripts\python -m app.verify
.venv/bin/python -m unittest discover tests # unit test
```

Baris terakhir `app.verify` harus `Ready to run (Vulkan GPU, CPU fallback).`

## Menggunakan aplikasi

1. Tunggu badge status menjadi **Siap**.
2. Pilih atau drag-and-drop file audio/video, atau rekam lewat tab **Rekam**.
3. Atur opsi:
   - **Bahasa audio**: lihat [Memilih bahasa](#memilih-bahasa) di bawah.
   - **Mode**: *Transkripsi* (bahasa asli) atau *Terjemahkan → Inggris*.
   - **Ketelitian (beam 1–8)**: 5 sudah paling seimbang; angka lebih besar sedikit lebih akurat tapi lebih lambat.
   - **Lewati hening (VAD)**: biarkan aktif.
   - **Bedakan pembicara** dan **Jumlah pembicara**: lihat [Bedakan pembicara](#bedakan-pembicara-speaker-diarization).
4. Klik **Mulai Transkripsi**. Rekaman 1 jam selesai ±3 menit di GPU RX 6500M.
5. Klik timestamp untuk memutar media dari titik itu. Salin hasil, atau unduh sebagai TXT / SRT (subtitle).

Bahasa tampilan diganti lewat tombol **ID / EN** di kanan atas (awalnya mengikuti bahasa browser), dan tema lewat tombol di sebelahnya. Semua pilihan ini tersimpan di browser.

### Memilih bahasa

- Saat kolom bahasa diklik, muncul 5 pilihan utama (Indonesia, Inggris, Deteksi otomatis, Melayu, Jawa). Ketik untuk mencari bahasa lain, misalnya "jepang", "sunda", atau kode `ja`.
- **Satu bahasa berlaku untuk seluruh file.** Memilih *Indonesia* berarti seluruh rekaman ditranskrip sebagai bahasa Indonesia; bahasa tidak berganti otomatis per kalimat.
- **Indonesia campur istilah Inggris aman.** Pilih *Indonesia*; kata seperti "follow up" atau "deadline" tetap tertulis Inggris.
- **Bagian panjang yang sepenuhnya berbahasa lain hasilnya tidak bisa ditebak** (bisa tetap bahasa aslinya, bisa diterjemahkan, bisa kacau). Potong file per bagian bahasa, lalu transkrip masing-masing.
- **Deteksi otomatis hanya menilai 30 detik pertama**, lalu memakai bahasa itu untuk seluruh file. Jika bahasanya diketahui, pilih manual: hasilnya lebih akurat.

**Peringatan bahasa.** Jika bahasa dipilih manual, setelah transkripsi selesai aplikasi mengecek 3 titik (awal, tengah, akhir ucapan; menambah ±4 detik):
- *Salah pilih*: semua titik terdeteksi bahasa lain. Muncul tombol **Transkrip ulang sebagai …**.
- *Rekaman campuran*: hanya sebagian titik yang berbeda. Ditunjukkan menit ke berapa, dengan saran memotong file.

Indonesia dan Melayu dianggap cocok karena Whisper sering tertukar di antara keduanya. Karena hanya 3 titik, perpindahan bahasa singkat di antaranya tidak terdeteksi, dan peringatan bisa keliru pada bagian yang penuh istilah asing atau musik; klik **Abaikan** jika hasilnya sudah baik. Ringkasan ini juga ada di panel **ⓘ Cara kerja pilihan bahasa** di aplikasi.

### Fitur lain

- **Pisahkan Audio** mengekstrak audio dari video menjadi WAV (terunduh otomatis). Opsional: *Mulai Transkripsi* bisa langsung memproses video.
- **Rekam dari mikrofon** hanya bisa dibuka lewat `http://127.0.0.1` / `localhost` atau HTTPS (aturan keamanan browser). Di [mode server](#mode-server-dipakai-bersama), pengguna lain tetap bisa mengunggah file rekaman.

## Mode server (dipakai bersama)

Jalankan di satu komputer; orang lain cukup membuka browser tanpa install apa pun.

```bash
# Linux
HOST=0.0.0.0 APP_RELOAD=0 bash scripts/start_app.sh
```

```bat
:: Windows
set HOST=0.0.0.0
set APP_RELOAD=0
scripts\start_app.bat
```

Pengguna lain membuka `http://<IP-server>:8000` (cek IP dengan `hostname -I` di Linux atau `ipconfig` di Windows). Izinkan port 8000 di firewall jika perlu.

- Transkripsi diproses **bergantian**, satu per satu di GPU, agar VRAM tidak habis. Permintaan lain menunggu giliran.
- **Tidak ada login.** Jalankan hanya di jaringan tepercaya (Wi-Fi ruang kelas, jaringan rumah), jangan dibuka ke internet.
- Isi `MAX_UPLOAD_MB` agar disk server tidak penuh.

## GPU yang didukung

Aplikasi memakai **Vulkan**, yang didukung semua vendor, jadi binary yang sama berjalan di AMD, NVIDIA, dan Intel. GPU dipilih otomatis: GPU diskrit lebih dulu, lalu iGPU, lalu CPU. Model turbo butuh ±1 GB VRAM.

| GPU | Driver | Catatan |
|---|---|---|
| AMD Radeon (RX, 680M/780M, dll.) | Windows: Adrenalin. Linux: Mesa RADV (bawaan) | Dites di RX 6500M: 1 jam audio ±3 menit |
| NVIDIA GeForce/RTX/Quadro | Driver resmi NVIDIA (bukan `nouveau`) | Seri GTX 900 ke atas |
| Intel Iris Xe / Arc / UHD (Gen 9+) | Windows: driver Intel. Linux: Mesa ANV (bawaan) | Lebih lambat dari GPU diskrit, tetap jauh lebih cepat dari CPU |
| Tanpa GPU / GPU sangat lama | – | Otomatis CPU, ±1,5× durasi audio |

## Model & kualitas transkripsi

Aplikasi memakai model terbaik yang ada di `models/`:

1. `ggml-large-v3-turbo-q5_0.bin` (diunduh otomatis). Jauh lebih akurat untuk bahasa Indonesia dan campuran Indonesia–Inggris.
2. `ggml-small.bin`, hanya jika model turbo tidak ada. Tidak diunduh otomatis.

Tanpa `ggml-silero-v5.1.2.bin`, opsi VAD diabaikan. Jika perlu mengunduh manual:

```bash
curl -L -o models/ggml-large-v3-turbo-q5_0.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
curl -L -o models/ggml-silero-v5.1.2.bin https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v5.1.2.bin
```

Pengaturan whisper yang dipakai (lihat `app/transcriber.py`):

- `-mc 0`: tidak memakai teks sebelumnya sebagai konteks, agar whisper tidak terjebak mengulang kalimat yang sama pada audio panjang.
- `-sns`: menyembunyikan token non-ucapan seperti `[musik]`.
- `--vad -vsd 500`: melewati hening dan memecah baris pada jeda ≥ 500 ms.

**Tips hasil terbaik:** pilih bahasa secara manual, pakai rekaman yang jelas (mikrofon dekat, minim gema), dan biarkan VAD aktif.

## Bedakan pembicara (speaker diarization)

Whisper hanya mengubah suara menjadi teks; ia tidak tahu siapa yang bicara. Fitur **Bedakan pembicara** memberi label `Pembicara 1`, `Pembicara 2`, dst. di setiap baris. Fitur ini memakai [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) dan dua model kecil yang ikut [disiapkan otomatis](#yang-disiapkan-otomatis). Model PyAnnote resmi di Hugging Face mewajibkan login, tetapi sherpa-onnx membagikan versi ONNX-nya di GitHub, jadi tidak perlu akun, token, maupun PyTorch.

**Cara pakai:** centang **Bedakan pembicara**, pilih **Jumlah pembicara** (*Otomatis (ditebak)*, atau angka 2–10 jika jumlah orangnya diketahui), lalu klik **Mulai Transkripsi**.

**Cara kerja:**
1. *Segmentasi*: audio dipotong per giliran bicara.
2. *Sidik suara*: tiap potongan diubah jadi deretan angka yang mewakili ciri suara (bukan isi ucapan, jadi tidak tergantung bahasa).
3. *Pengelompokan*: potongan yang suaranya mirip dianggap orang yang sama.
4. *Dicocokkan ke teks*: whisper memberi waktu per kata, jadi satu baris yang berisi dua orang ("…gitu ya?" "Iya betul") dipecah di titik pergantian pembicara.

**Akurasi (benchmark).** 8 model pengenal suara dibandingkan pada 6 percakapan uji buatan (2–5 orang, 5 menit, ±⅓ giliran berupa jawaban pendek < 2 detik) dari pembicara dataset LibriSpeech, sehingga siapa bicara kapan diketahui pasti. Model yang lebih besar (TitaNet-large, WeSpeaker ResNet152/293) ternyata tidak lebih akurat dan jauh lebih lambat. Hasil mode *Otomatis*, dihitung per kata pada ±4.600 kata:

| | Versi awal (TitaNet-small) | Sekarang (ERes2Net, dipotong per kata) |
|---|---|---|
| Kata dengan label pembicara benar | 65,2% | **90,4%** |
| Kata di jawaban pendek (< 2 detik) | 41,9% | **63,1%** |
| Jumlah orang tertebak (benar: 2, 3, 3, 4, 4, 5) | 2, 2, 2, 3, 2, 3 | **2, 3, 3, 4, 4, 4** |

Benchmark ini memakai rekaman bacaan bahasa Inggris yang bersih. Rekaman diskusi atau kelas (mikrofon jauh, gema, saling potong) umumnya lebih sulit.

**Yang perlu diketahui:**
- **Tebakan jumlah orang bisa meleset**, terutama jika orangnya banyak atau suaranya mirip. Jika tahu jumlahnya, isi angkanya. Sensitivitasnya diatur `DIARIZATION_THRESHOLD` (bawaan 1.1; lebih kecil = lebih banyak pembicara).
- **Jawaban sangat pendek masih sering tertukar** (±63% benar), karena potongan suara < 2 detik terlalu sedikit untuk dikenali.
- **Pembicara kecil digabung** (hanya mode *Otomatis*). Rekaman yang bising bisa membuat potongan kecil terbaca sebagai orang baru; pada satu diskusi uji 56 menit sempat muncul 27 "pembicara". Pembicara dengan porsi bicara < 2% (`DIARIZATION_MIN_SHARE`) digabung ke orang yang bicara tepat sebelum atau sesudahnya, sehingga diskusi itu menjadi 6 pembicara. Akibatnya, orang yang hanya bicara sangat sedikit (< 1 menit dalam 1 jam) bisa ikut tergabung.
- **Berjalan di CPU** setelah transkripsi selesai, menambah ±8 detik per menit audio (diskusi 56 menit: +7,7 menit di Ryzen 5 7535HS). Library ini tidak punya jalur GPU AMD di Linux.
- **Label anonim**, bukan nama asli. Nomor diberikan sesuai urutan orang pertama kali bicara.

## Konfigurasi (environment variable)

Semua opsional; nilai bawaan sudah cocok untuk pemakaian biasa.

| Variabel | Default | Keterangan |
|---|---|---|
| `HOST` | `127.0.0.1` | `0.0.0.0` agar bisa diakses dari jaringan |
| `PORT` | `8000` | Jika terpakai, otomatis mencari port berikutnya |
| `APP_RELOAD` | `1` | Server restart otomatis saat kode berubah; isi `0` untuk mode server |
| `MAX_UPLOAD_MB` | `0` (tanpa batas) | Batas ukuran upload dalam MB, berlaku di UI dan server |
| `WHISPER_MODEL` | `large-v3-turbo-q5_0` jika ada, selain itu `small` | Nama model → `models/ggml-<nama>.bin` |
| `WHISPER_MODEL_PATH` | dari `WHISPER_MODEL` | Path lengkap file model |
| `WHISPER_VAD_MODEL_PATH` | `models/ggml-silero-v5.1.2.bin` | Model VAD |
| `WHISPER_CLI` | Windows: `build-vulkan/bin/Release/whisper-cli.exe`<br>Linux: `build-linux/bin/whisper-cli` | Path binary whisper |
| `WHISPER_GPU_DEVICE` | `auto` | `auto` = GPU diskrit → iGPU → CPU; atau nomor GPU Vulkan (`0`, `1`, …) |
| `WHISPER_TIMEOUT_SECONDS` | `3600` | Batas waktu satu transkripsi |
| `DIARIZATION_THRESHOLD` | `1.1` | Sensitivitas tebakan jumlah pembicara; lebih kecil = lebih banyak pembicara (1.0 mulai memecah satu orang jadi dua, 1.2 mulai menggabungkan orang berbeda) |
| `DIARIZATION_MIN_SHARE` | `0.02` | Pembicara dengan porsi bicara di bawah ini digabung ke pembicara terdekat (mode *Otomatis*) |
| `WHISPER_WINDOWS_URL` / `WHISPER_WINDOWS_SHA256` | GitHub Release project ini | Sumber unduhan whisper.cpp Windows |

Cara mengisi: Linux `WHISPER_GPU_DEVICE=0 bash scripts/start_app.sh`; Windows CMD `set WHISPER_GPU_DEVICE=0` lalu jalankan script; PowerShell `$env:WHISPER_GPU_DEVICE="0"`.

Nomor GPU biasanya tidak perlu diatur. Untuk melihat daftarnya, jalankan whisper-cli sekali dan cari baris `ggml_vulkan: 0 = ...`, `ggml_vulkan: 1 = ...`.

## API

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/health` | Status backend, model, GPU, dan fitur bedakan pembicara |
| POST | `/api/warmup` | Cek kesiapan backend |
| POST | `/api/extract-audio` | Form `file` → unduhan WAV |
| POST | `/api/transcribe` | Lihat di bawah |

Form `/api/transcribe`:

| Field | Nilai |
|---|---|
| `file` | File audio/video |
| `language` | Kode Whisper (`id`, `en`, `ja`, `jw` untuk Jawa, `su` untuk Sunda, …; daftar lengkap di `WHISPER_LANGUAGES`, `app/config.py`) atau `auto` |
| `task` | `transcribe` atau `translate` |
| `beam_size` | 1–8 |
| `vad_filter` | `true` / `false` |
| `diarize` | `true` / `false` |
| `num_speakers` | `0` = otomatis, atau 1–20 |

Respons juga berisi `language_checks`: daftar `{at, language, probability}` hasil cek bahasa di 3 titik (kosong jika `language=auto`).

```bash
curl -F file=@diskusi.mp3 -F language=id http://127.0.0.1:8000/api/transcribe
```

## Struktur project

```text
app/
  config.py          Konfigurasi, path, environment variable
  main.py            FastAPI app & entrypoint (python -m app.main)
  transcriber.py     Menjalankan whisper-cli, fallback GPU/CPU, antrean GPU, cek bahasa
  audio.py           Konversi audio/video ke WAV 16 kHz (PyAV, tanpa FFmpeg)
  diarization.py     Bedakan pembicara (sherpa-onnx, CPU)
  verify.py          Cek dependensi, binary, dan model
  bootstrap.py       Setup otomatis (hanya library standar Python)
static/              Frontend (index.html)
tests/               Unit test
requirements/
  base.txt           Dependensi Python
scripts/
  start_app.bat      Launcher Windows
  start_app.sh       Launcher Linux
  build_whisper.sh   Build whisper.cpp Vulkan untuk Linux
  package.sh         Membuat zip whisper.cpp Windows (untuk maintainer)
```

Folder `.venv/`, `build-vulkan/`, `build-linux/`, `models/`, `third_party/`, `uploads/`, dan `dist/` dibuat saat dijalankan dan tidak di-commit.

## Cakupan & batasan

Baca bagian ini sebelum memakai hasilnya untuk catatan penting.

### Tidak didukung

| Fitur | Keterangan / alternatif |
|---|---|
| Transkripsi real-time (live) | Rekaman mikrofon baru diproses setelah perekaman dihentikan. |
| Terjemahan ke selain bahasa Inggris | Batasan Whisper; misalnya Inggris → Indonesia tidak bisa. |
| Ganti bahasa otomatis per kalimat | Satu bahasa per file; potong file per bagian bahasa ([Memilih bahasa](#memilih-bahasa)). |
| Nama asli pembicara | Hanya label anonim *Pembicara 1, 2, …*. |
| Riwayat hasil | Hasil hilang saat halaman di-refresh atau ditutup. Unduh TXT/SRT dulu. |
| Edit teks, ringkasan otomatis, ekspor DOCX/PDF | Salin atau unduh TXT, lalu olah di aplikasi lain. |
| Login, hak akses, HTTPS | Siapa pun di jaringan bisa memakai server; jangan dibuka ke internet. |
| Membatalkan transkripsi | Menutup atau me-refresh halaman **tidak** menghentikan proses di server; GPU tetap terpakai sampai selesai dan hasilnya hilang. Aplikasi memberi peringatan sebelum halaman ditutup. |

### Batasan teknis

| Area | Batasan | Yang bisa dilakukan |
|---|---|---|
| Akurasi | Whisper bisa salah menulis nama orang, istilah teknis, singkatan, dan angka. Di bagian hening/musik kadang muncul teks "halusinasi". | Biarkan VAD aktif, dan periksa ulang hasil untuk dokumen penting. |
| Bahasa daerah | Jawa dan Sunda jauh lebih lemah dari Indonesia/Inggris karena data latih Whisper sedikit. | Memilih *Indonesia* sering memberi hasil lebih baik. |
| Bahasa & pembicara | Lihat [Memilih bahasa](#memilih-bahasa) dan [Bedakan pembicara](#bedakan-pembicara-speaker-diarization). | – |
| Ketelitian (beam) | Maksimal 8 (batas whisper.cpp). | Di atas 5 peningkatannya sangat kecil. |
| Antrean | Satu transkripsi di GPU pada satu waktu; posisi antrean tidak ditampilkan. | Di mode server, pengguna lain melihat timer berjalan lebih lama sampai gilirannya. |
| Progres | Persentase hanya untuk upload; saat transkripsi hanya tampil waktu berjalan. | Perkiraan: ±3 menit per jam audio di GPU, ±1,5× durasi audio di CPU. |
| Waktu maksimal | 1 jam per file (`WHISPER_TIMEOUT_SECONDS`). File sangat panjang di CPU bisa melewatinya. | Naikkan nilainya, atau pakai GPU. |
| Ruang disk | Selama diproses, server menyimpan file asli + WAV sementara (±115 MB per jam audio). | Di mode server, isi `MAX_UPLOAD_MB`. |
| Gagal di GPU | Jika whisper gagal, aplikasi mencoba ulang di GPU 0 lalu CPU, termasuk untuk error yang bukan karena GPU. | Pesan error bisa muncul lebih lama dari seharusnya. |
| Pesan error | Pesan error dari server selalu berbahasa Indonesia, walau tampilan diset ke EN. | – |

## Lisensi, privasi & atribusi

- Kode project ini berlisensi **MIT** (lihat [LICENSE](LICENSE)): boleh dipakai, diubah, dan dibagikan, termasuk untuk keperluan komersial, asal pemberitahuan hak cipta dan lisensinya tetap disertakan.
- Komponen pihak ketiga (model AI, whisper.cpp, sherpa-onnx, library Python) dan lisensinya tercantum di [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Semuanya MIT, Apache-2.0, atau BSD.
- **Privasi:** audio diproses di komputer yang menjalankan aplikasi. File upload dan WAV sementara dihapus setelah diproses, dan hasil transkrip tidak disimpan di server, hanya tampil di browser pengguna.
- **Minta izin sebelum merekam.** Merekam kelas, seminar, atau diskusi berarti memproses data pribadi (suara orang lain). Minta izin pembicara dan peserta, jelaskan tujuannya, dan hapus rekaman setelah tidak diperlukan. Di Indonesia, ini sejalan dengan UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi.
- Jika transkrip diolah lagi di layanan lain (misalnya chatbot AI untuk merangkum), teksnya ikut keluar dari komputer. Pastikan penyelenggara dan pembicara mengizinkannya, terutama untuk materi tertutup seperti pelatihan berbayar.

## Troubleshooting

**`[setup] GAGAL: ...` saat pertama dijalankan**
Pesan di bawahnya menyebutkan penyebab dan perbaikannya. Yang umum:
- *Gagal mengunduh*: cek koneksi internet, lalu jalankan ulang.
- *Tool berikut belum terpasang* / *Butuh python3-venv* (Linux selain Debian/Ubuntu): install paket yang disebutkan lewat package manager distro.
- *Install Visual C++ Redistributable belum berhasil* (Windows): prompt administrator ditolak atau gagal. Install dari link yang ditampilkan, lalu jalankan ulang.

**Windows: muncul *Windows protected your PC* atau antivirus memblokir file**
Windows memperingatkan script dan program yang diunduh dari internet tanpa tanda tangan digital. Klik **More info → Run anyway**. Jika Windows Defender mengkarantina `whisper-cli.exe`, pulihkan file itu, atau hapus folder `build-vulkan\` lalu jalankan ulang `start_app.bat`.

**Windows: `Python tidak ditemukan dan tidak bisa diinstall otomatis`**
PC tidak punya `winget` (Windows lama) atau instalasinya gagal. Install Python dari python.org, centang *Add python.exe to PATH*, lalu jalankan ulang `start_app.bat`.

**Status tidak pernah "Siap" / `503 Service Unavailable`**
Jalankan `.venv/bin/python -m app.verify` (Windows: `.venv\Scripts\python -m app.verify`) untuk melihat file yang hilang.

**`whisper.cpp gagal (exit ...)`**
Pesan error menampilkan log whisper. Penyebab umum:
- VRAM tidak cukup: tutup aplikasi lain yang memakai GPU, atau pilih GPU lain dengan `WHISPER_GPU_DEVICE`.
- Driver Vulkan tidak ada: Linux `sudo apt install mesa-vulkan-drivers`; Windows update driver GPU. Aplikasi seharusnya otomatis pindah ke CPU.

**Transkripsi lambat**
Kemungkinan berjalan di CPU. Di Windows, jika ada file `build-vulkan/bin/Release/CPU_ONLY.txt`, berarti yang terpasang whisper.cpp versi CPU karena build Vulkan belum tersedia saat setup. Cek apakah GPU terbaca, misalnya di Linux:
```bash
build-linux/bin/whisper-cli -m models/ggml-large-v3-turbo-q5_0.bin -f contoh.wav -dev 1 2>&1 | grep -i vulkan
```
Baris `using Vulkan1 backend` berarti GPU dipakai. Jika tidak ada, cek driver Vulkan dan `WHISPER_GPU_DEVICE`.

**Hasil mengulang kalimat yang sama terus-menerus**
Pastikan memakai versi terbaru project ini dan model turbo.

**Banyak teks aneh di bagian hening**
Pastikan `models/ggml-silero-v5.1.2.bin` ada dan opsi VAD dicentang.

**Port 8000 sudah dipakai**
Aplikasi otomatis memakai port berikutnya (8001, 8002, …); lihat alamat yang dicetak di terminal.

**Tampilan aneh, fitur baru tidak muncul, atau error `Beam size harus berada di antara 1 dan 8`**
Browser masih memakai halaman lama. Refresh dengan `Ctrl+F5`.

**`Kode bahasa tidak dikenal`**
Hanya terjadi lewat API. Lihat nilai `language` di [API](#api).

## Untuk maintainer: binary whisper Windows

Bagian ini hanya untuk pemilik repository; pengguna biasa bisa melewatinya.

Di Windows, setup otomatis mengunduh `whisper-cli.exe` siap pakai dari rilis [`whisper-vulkan-bd9985c`](https://github.com/theCrudify/01.-Audio-Transcrypt/releases/tag/whisper-vulkan-bd9985c), karena build whisper.cpp di Windows butuh Visual Studio + Vulkan SDK. [Rilis resmi whisper.cpp](https://github.com/ggml-org/whisper.cpp/releases) tidak punya versi Vulkan untuk Windows (hanya CPU, CUDA, BLAS). Jika rilis di project ini tidak bisa diakses, Windows otomatis memakai versi CPU resmi, hanya lebih lambat.

Rilis ini **sudah tersedia**. Langkah di bawah hanya perlu diulang jika versi whisper.cpp diganti (dijalankan di Linux):

1. Jalankan `bash scripts/package.sh`. Hasilnya `dist/whisper-vulkan-windows-x64.zip` (±18 MB), berisi **hanya** `whisper-cli.exe` + DLL whisper.cpp/ggml (MIT) dan teks lisensinya. DLL runtime Microsoft sengaja tidak disertakan; setup menginstallnya dari Microsoft.
2. Upload ke rilis dengan tag baru yang sesuai commit whisper.cpp, misalnya `gh release create whisper-vulkan-<commit> dist/whisper-vulkan-windows-x64.zip`.
3. Perbarui `WINDOWS_BINARY_URL` dan `WINDOWS_BINARY_SHA256` di `app/bootstrap.py` sesuai file yang **di-upload** (sha256 berubah setiap kali zip dibuat ulang). Jangan menimpa zip di rilis lama, karena pengguna versi lama masih memakai sha256 lama.

Repository harus **public**, karena unduhan dari repo private tanpa login gagal (404).
