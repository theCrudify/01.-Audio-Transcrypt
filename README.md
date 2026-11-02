# Local AI Transcription Studio

Aplikasi web untuk mentranskrip audio dan video **sepenuhnya di komputer sendiri** (tanpa cloud), memakai [whisper.cpp](https://github.com/ggerganov/whisper.cpp) dengan akselerasi GPU Vulkan. Berjalan di **Windows dan Linux**, di laptop pribadi maupun sebagai server untuk satu tim.

## Mulai cepat

Repository ini hanya berisi kode (±200 KB). File besar seperti model, whisper.cpp, dan library Python **disiapkan otomatis saat pertama dijalankan** (±600 MB, sekali saja; lihat [Setup otomatis](#setup-otomatis-saat-pertama-dijalankan)). Yang perlu dilakukan setelah clone:

### Linux (Debian/Ubuntu)

```bash
# 1. Prasyarat, sekali saja
sudo apt install python3 python3-venv git build-essential cmake libvulkan-dev glslc mesa-vulkan-drivers

# 2. Clone lalu jalankan
git clone https://github.com/theCrudify/01.-Audio-Transcrypt.git
cd 01.-Audio-Transcrypt
bash scripts/start_app.sh
```

Run pertama ±4 menit: install library Python, build whisper.cpp, unduh model. **Model tidak perlu diunduh manual**; lihat [Model terunduh otomatis](#model-terunduh-otomatis).

Contoh output run pertama:

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

### Windows

1. Install **Python 3.10+** dari [python.org](https://www.python.org/downloads/) dan centang *Add python.exe to PATH*.
2. Clone repository (atau *Code → Download ZIP* di GitHub lalu ekstrak).
3. Double-click `scripts\start_app.bat`.

Run pertama ±2–5 menit: install library Python, unduh whisper.cpp siap pakai dan model. Windows tidak perlu Visual Studio atau tool build. Model juga [terunduh otomatis](#model-terunduh-otomatis).

### Setelah itu

Buka http://127.0.0.1:8000, tunggu badge **Siap**, lalu upload file. Hentikan dengan `Ctrl+C`. Run berikutnya langsung start karena semua file sudah ada.

| | Windows | Linux |
|---|---|---|
| Prasyarat manual | Python saja | Python + tool build (perintah `apt` di atas) |
| whisper.cpp | Diunduh siap pakai dari [GitHub Release](https://github.com/theCrudify/01.-Audio-Transcrypt/releases) | Di-build di komputer itu (cocok dengan versi sistem) |
| Model, library Python, aplikasi | Sama | Sama |

Tidak mau install Python? Pakai [paket siap pakai](#cara-1--paket-siap-pakai-tanpa-install). Setup gagal? Lihat [Troubleshooting](#troubleshooting).

## Daftar isi

1. [Fitur](#fitur)
2. [Pilih cara pakai](#pilih-cara-pakai)
3. [Cara 1 — Paket siap pakai (tanpa install)](#cara-1--paket-siap-pakai-tanpa-install)
4. [Cara 2 — Dari source code](#cara-2--dari-source-code)
5. [Mode server (dipakai bersama)](#mode-server-dipakai-bersama)
6. [Menggunakan aplikasi](#menggunakan-aplikasi)
7. [GPU yang didukung](#gpu-yang-didukung)
8. [Model & kualitas transkripsi](#model--kualitas-transkripsi)
9. [Konfigurasi (environment variable)](#konfigurasi-environment-variable)
10. [Speaker diarization (bedakan pembicara)](#speaker-diarization-bedakan-pembicara)
11. [Membuat paket siap pakai](#membuat-paket-siap-pakai)
12. [API](#api)
13. [Struktur project](#struktur-project)
14. [Cakupan & batasan](#cakupan--batasan)
15. [Troubleshooting](#troubleshooting)

## Fitur

- Upload audio/video lewat browser: `aac, flac, m4a, mkv, mov, mp3, mp4, ogg, opus, wav, webm` (tanpa batas ukuran; bisa dibatasi lewat `MAX_UPLOAD_MB`).
- Fokus bahasa Indonesia & Inggris (termasuk campuran istilah Inggris); ±100 bahasa lain lewat kolom pencarian, atau deteksi otomatis.
- Peringatan otomatis jika bahasa yang dipilih tidak cocok dengan audio, atau rekaman ternyata campuran bahasa.
- Mode transkripsi, atau terjemahan langsung ke bahasa Inggris.
- Timestamp per segmen (klik untuk memutar); salin atau unduh hasil sebagai TXT / SRT.
- Rekam langsung dari mikrofon.
- Tampilan ID/EN, responsif (HP, tablet, laptop), tema terang/gelap.
- Ekstrak audio dari video menjadi file WAV.
- GPU Vulkan (AMD, NVIDIA, Intel). Jika GPU gagal, otomatis pindah ke GPU lain lalu ke CPU.
- VAD (Voice Activity Detection) untuk melewati bagian hening dan mengurangi teks "halusinasi".
- Bedakan pembicara (*Pembicara 1, 2, …*) secara lokal, tanpa login/token; jumlah pembicara bisa ditebak otomatis atau diisi sendiri.
- Tidak butuh Anaconda, FFmpeg, atau koneksi internet saat dipakai.

Sebelum dipakai untuk pekerjaan penting, baca [Cakupan & batasan](#cakupan--batasan).

## Pilih cara pakai

| Kebutuhan | Cara |
|---|---|
| Pakai saja, tanpa install Python / apa pun | [Cara 1 — Paket siap pakai](#cara-1--paket-siap-pakai-tanpa-install) |
| Mengembangkan / mengubah kode | [Cara 2 — Dari source code](#cara-2--dari-source-code) |
| Satu komputer dipakai banyak orang lewat browser | [Mode server](#mode-server-dipakai-bersama) (bisa digabung dengan Cara 1 atau 2) |

## Cara 1 — Paket siap pakai (tanpa install)

Paket sudah berisi Python, semua library, whisper.cpp, dan model. **Tidak perlu Anaconda, Python, atau pip.**

### Windows

1. Ekstrak `AudioTranscrypt-windows.zip` (misalnya ke `C:\AudioTranscrypt`).
2. Double-click `start.bat`.
3. Buka alamat yang muncul di jendela terminal, biasanya http://127.0.0.1:8000.

Jangan tutup jendela terminal selama aplikasi dipakai.

### Linux

```bash
tar -xzf AudioTranscrypt-linux.tar.gz
cd AudioTranscrypt-linux
./start.sh
```

Lalu buka http://127.0.0.1:8000.

Syarat Linux: glibc 2.38+ (Ubuntu 24.04+, Debian 13+, Fedora 39+) dan driver Vulkan Mesa (`mesa-vulkan-drivers`, biasanya sudah terpasang). Tanpa driver Vulkan, aplikasi tetap jalan memakai CPU (lebih lambat).

## Cara 2 — Dari source code

### Prasyarat (install manual sekali)

| | Windows | Linux (Debian/Ubuntu) |
|---|---|---|
| Python 3.10+ | Dari [python.org](https://www.python.org/downloads/) (centang *Add python.exe to PATH*). Anaconda juga bisa, tapi **tidak wajib**. | `sudo apt install python3 python3-venv` |
| Tool build whisper.cpp | Tidak perlu (binary diunduh) | `sudo apt install git build-essential cmake libvulkan-dev glslc mesa-vulkan-drivers` |
| Internet | Hanya saat pertama dijalankan | sama |

### Setup otomatis saat pertama dijalankan

File besar **tidak disimpan di git** (sudah di-filter `.gitignore`), supaya repository tetap kecil (±200 KB). `scripts/start_app.sh` / `.bat` menjalankan `python -m app.bootstrap` sebelum server start. Script ini menyiapkan:

| Yang disiapkan | Ukuran | Sumber | Caranya |
|---|---|---|---|
| `.venv/` + dependensi Python | ±230 MB | PyPI (`requirements/base.txt`) | Dibuat otomatis; diinstall ulang jika `requirements/base.txt` berubah |
| `build-vulkan/bin/Release/` (Windows) | ±60 MB | [GitHub Release project ini](https://github.com/theCrudify/01.-Audio-Transcrypt/releases) | Diunduh lalu diekstrak |
| `build-linux/bin/whisper-cli` (Linux) | – | Source [whisper.cpp-amd](https://github.com/lemonade-sdk/whisper.cpp-amd) commit `bd9985c` | Di-clone ke `third_party/` lalu di-build (beberapa menit) |
| `models/ggml-large-v3-turbo-q5_0.bin` | ±550 MB | Hugging Face | Diunduh |
| `models/ggml-silero-v5.1.2.bin` | ±1 MB | Hugging Face | Diunduh |
| `models/pyannote-segmentation-3.0.onnx` + `models/nemo_en_titanet_small.onnx` | ±46 MB | GitHub Release sherpa-onnx | Diunduh (model bedakan pembicara) |

Yang sudah ada dilewati, jadi run berikutnya langsung start (±1 detik). Script tidak pernah menjalankan `sudo`; jika tool sistem belum ada, script berhenti dan menampilkan perintah `apt` yang perlu dijalankan. Setiap unduhan dicek **sha256**: unduhan yang terputus atau rusak tidak dipakai, cukup jalankan ulang. Jika `WHISPER_CLI` atau `WHISPER_MODEL_PATH` diisi, bagian itu dilewati.

#### Model terunduh otomatis

Ya, **model diunduh otomatis** saat `start_app.sh` / `start_app.bat` dijalankan pertama kali. Tidak perlu mengunduh apa pun secara manual, dan tidak perlu login ke Hugging Face atau situs lain.

| File | Ukuran | Sumber | Fungsi |
|---|---|---|---|
| `models/ggml-large-v3-turbo-q5_0.bin` | 574 MB | Hugging Face `ggerganov/whisper.cpp` | Model transkripsi utama |
| `models/ggml-silero-v5.1.2.bin` | 0,9 MB | Hugging Face `ggml-org/whisper-vad` | Model VAD (melewati bagian hening) |
| `models/pyannote-segmentation-3.0.onnx` | 6 MB | GitHub Release `k2-fsa/sherpa-onnx` | Bedakan pembicara: memotong giliran bicara |
| `models/nemo_en_titanet_small.onnx` | 40 MB | GitHub Release `k2-fsa/sherpa-onnx` | Bedakan pembicara: mengenali suara |

- Progres unduhan tampil di terminal (`45%  258 / 574 MB`).
- Setiap file dicek dengan **sha256** (sama dengan yang dipublikasikan sumbernya). Unduhan yang terputus atau rusak dibuang, bukan dipakai. Jalankan ulang script untuk mengunduh lagi (dari awal, tidak dilanjutkan).
- Hanya sekali: jika file sudah ada di `models/`, unduhan dilewati.
- Model `ggml-small.bin` **tidak** ikut diunduh; aplikasi selalu memakai model turbo bila tersedia.

Model **tidak** diunduh jika:
- file sudah ada di `models/` (misalnya disalin dari komputer lain; cara untuk komputer tanpa internet), atau
- `WHISPER_MODEL_PATH` diisi (memakai model sendiri).

Bisa juga dijalankan terpisah tanpa start server:

```bash
python3 -m app.bootstrap          # Windows: python -m app.bootstrap
```

Saat dijalankan dari source, server otomatis restart setiap kali kode berubah (`APP_RELOAD=1`).

### Cek setup & test

`start_app.sh` / `start_app.bat` sudah menjalankan pengecekan ini otomatis sebelum server start. Untuk menjalankannya manual:

```bash
.venv/bin/python -m app.verify              # Windows: .venv\Scripts\python -m app.verify
.venv/bin/python -m unittest discover tests # unit test
```

Output terakhir `app.verify` harus `Ready to run (Vulkan GPU, CPU fallback).`

## Mode server (dipakai bersama)

Jalankan di satu komputer, orang lain cukup membuka browser — mereka tidak perlu download apa pun.

```bash
# Linux (source)
HOST=0.0.0.0 APP_RELOAD=0 bash scripts/start_app.sh
# Linux (paket)
HOST=0.0.0.0 ./start.sh
```

```bat
:: Windows (source atau paket)
set HOST=0.0.0.0
set APP_RELOAD=0
scripts\start_app.bat        :: atau start.bat di paket
```

Pengguna lain membuka `http://<IP-server>:8000` (cek IP dengan `hostname -I` di Linux atau `ipconfig` di Windows). Izinkan port 8000 di firewall jika perlu.

Catatan:
- Transkripsi diproses **bergantian** (satu per satu di GPU) agar VRAM tidak habis; permintaan lain menunggu giliran.
- **Tidak ada login.** Jalankan hanya di jaringan tepercaya (LAN kantor/VPN), jangan langsung ke internet.

## Menggunakan aplikasi

Tampilan menyesuaikan HP, tablet, dan laptop. Bahasa antarmuka bisa diganti lewat tombol **ID / EN** di kanan atas (otomatis mengikuti bahasa browser saat pertama dibuka), dan tema terang/gelap lewat tombol di sebelahnya (default mengikuti sistem). Pilihan bahasa, tema, dan pengaturan transkripsi tersimpan di browser.

1. Tunggu badge status berubah menjadi **Siap**.
2. Pilih atau drag-and-drop file audio/video, atau rekam lewat tab **Rekam**.
3. Atur opsi:
   - **Bahasa audio**: saat diklik muncul 5 pilihan utama (Indonesia, Inggris, Deteksi otomatis, Melayu, Jawa). Ketik nama bahasa untuk mencari ±100 bahasa lain yang didukung Whisper, misalnya "jepang", "sunda", "arab" (nama Indonesia, Inggris, atau kode `ja` bisa dipakai). Untuk percakapan campuran Indonesia–Inggris pilih *Indonesia*. Memilih bahasa secara eksplisit lebih akurat daripada *Deteksi otomatis*.
   - **Mode**: *Transkripsi* (bahasa asli) atau *Terjemahkan → Inggris*.
   - **Ketelitian (beam 1–8)**: 5 adalah keseimbangan terbaik; lebih besar sedikit lebih akurat tapi lebih lambat.
   - **Lewati hening (VAD)**: biarkan aktif.
   - **Bedakan pembicara** + **Jumlah pembicara**: lihat [Speaker diarization](#speaker-diarization-bedakan-pembicara).
4. Klik **Mulai Transkripsi**. File 1 jam ±3 menit di GPU RX 6500M.
5. Klik timestamp untuk memutar media dari titik itu. Salin hasil, atau unduh sebagai TXT / SRT (subtitle).

**Peringatan bahasa**: jika bahasa audio dipilih manual, setelah transkripsi selesai server mengecek bahasa di awal, tengah, dan akhir bagian yang berisi ucapan (klip 30 detik, +±4 detik total). Ada dua jenis peringatan:
- *Salah pilih*: semua titik terdeteksi bahasa lain → tombol **Transkrip ulang sebagai …**.
- *Rekaman campuran*: hanya sebagian titik yang berbeda → diberi tahu menit ke berapa; sarannya potong file per bagian.

Indonesia ↔ Melayu dianggap cocok karena Whisper sering tertukar di antara keduanya. Panel **ⓘ Cara kerja pilihan bahasa** di aplikasi merangkum catatan di bawah.

### Catatan: cara kerja pilihan bahasa

- **Satu bahasa dikunci untuk seluruh file.** Memilih *Indonesia* berarti whisper memakai bahasa Indonesia dari awal sampai akhir; tidak ada perpindahan otomatis per kalimat. Kartu *Bahasa* di hasil menandainya sebagai "dikunci (dipilih)".
- **Campuran Indonesia + istilah Inggris aman.** Pilih *Indonesia*; istilah seperti "follow up" atau "deadline" tetap tertulis Inggris.
- **Bagian panjang yang sepenuhnya berbahasa lain tidak bisa ditebak hasilnya** (bisa tetap tertulis bahasa aslinya, bisa diterjemahkan, bisa kacau). Potong file per bagian lalu transkrip masing-masing.
- **Deteksi otomatis hanya menilai 30 detik pertama**, lalu memakai bahasa itu untuk seluruh file. Rekaman yang dibuka dengan bahasa Inggris akan ditranskrip sebagai Inggris semuanya.
- Pengecekan awal/tengah/akhir hanya sampel 3 titik; perpindahan bahasa singkat di antara titik itu tidak akan terdeteksi.


**Pisahkan Audio**: mengekstrak audio video menjadi WAV yang terunduh otomatis dan menggantikan file yang dipilih. Ini opsional — *Mulai Transkripsi* bisa langsung memproses video.

**Rekam dari mikrofon** hanya bisa di `http://127.0.0.1`/`localhost` atau HTTPS (aturan keamanan browser). Pengguna di mode server yang membuka `http://<IP-server>` tetap bisa mengunggah file rekaman.

## GPU yang didukung

Aplikasi memakai **Vulkan**, standar grafis yang didukung semua vendor, jadi binary yang sama berjalan di AMD, NVIDIA, dan Intel. GPU dipilih otomatis saat transkripsi pertama: GPU diskrit lebih dulu, lalu iGPU, lalu CPU.

| GPU | Syarat driver | Catatan |
|---|---|---|
| AMD Radeon (RX, 680M/780M, dll.) | Windows: Adrenalin. Linux: Mesa RADV (bawaan) | Dites di RX 6500M: 1 jam audio ±3 menit |
| NVIDIA GeForce/RTX/Quadro | Windows/Linux: driver resmi NVIDIA (bukan `nouveau`) | Seri GTX 900 ke atas |
| Intel Iris Xe / Arc / UHD (Gen 9+) | Windows: driver Intel. Linux: Mesa ANV (bawaan) | Lebih lambat dari GPU diskrit, tetap jauh lebih cepat dari CPU |
| Tanpa GPU / GPU sangat lama | – | Otomatis CPU; model turbo ±1,5× durasi audio |

Laptop dengan dua GPU (misalnya Intel + NVIDIA) otomatis memakai GPU diskrit. Model turbo butuh ±1 GB VRAM.

## Model & kualitas transkripsi

Taruh model di folder `models/`. Aplikasi otomatis memakai model terbaik yang tersedia:

| File | Ukuran | Fungsi |
|---|---|---|
| [`ggml-large-v3-turbo-q5_0.bin`](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin) | ~550 MB | **Direkomendasikan.** Jauh lebih akurat untuk Indonesia & campuran Indonesia–Inggris. Muat di GPU 4 GB. |
| [`ggml-small.bin`](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin) | ~490 MB | Fallback jika turbo tidak ada. |
| [`ggml-silero-v5.1.2.bin`](https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v5.1.2.bin) | ~1 MB | Model VAD. Tanpa file ini, opsi VAD diabaikan. |

Model turbo dan VAD **diunduh otomatis** oleh [setup otomatis](#setup-otomatis-saat-pertama-dijalankan). Unduh manual hanya jika perlu (misalnya komputer tanpa internet, file disalin dari komputer lain):

```bash
curl -L -o models/ggml-large-v3-turbo-q5_0.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
curl -L -o models/ggml-silero-v5.1.2.bin https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v5.1.2.bin
```

Pengaturan whisper yang dipakai (lihat `app/transcriber.py`):

- `-mc 0`: tidak memakai teks sebelumnya sebagai konteks. Mencegah whisper terjebak mengulang kalimat yang sama ratusan kali pada audio panjang.
- `-sns`: menyembunyikan token non-ucapan seperti `[musik]`.
- `--vad -vsd 500`: melewati hening, memecah segmen pada jeda ≥ 500 ms.

Tips hasil terbaik: pilih bahasa secara eksplisit, gunakan rekaman yang jelas (mic dekat, minim gema), dan biarkan VAD aktif.

## Konfigurasi (environment variable)

| Variabel | Default | Keterangan |
|---|---|---|
| `HOST` | `127.0.0.1` | `0.0.0.0` agar bisa diakses dari jaringan |
| `PORT` | `8000` | Jika terpakai, otomatis mencari port berikutnya |
| `APP_RELOAD` | `1` (`0` di paket) | Auto-restart saat kode berubah; set `0` untuk server |
| `WHISPER_MODEL` | `large-v3-turbo-q5_0` jika ada, selain itu `small` | Nama model → `models/ggml-<nama>.bin` |
| `WHISPER_MODEL_PATH` | dari `WHISPER_MODEL` | Path lengkap file model |
| `WHISPER_VAD_MODEL_PATH` | `models/ggml-silero-v5.1.2.bin` | Model VAD |
| `WHISPER_CLI` | Windows: `build-vulkan/bin/Release/whisper-cli.exe`<br>Linux: `build-linux/bin/whisper-cli` | Path binary whisper |
| `WHISPER_GPU_DEVICE` | `auto` | `auto` memilih GPU diskrit → iGPU → CPU; atau isi nomor GPU Vulkan (`0`, `1`, …) |
| `WHISPER_TIMEOUT_SECONDS` | `3600` | Batas waktu satu transkripsi |
| `MAX_UPLOAD_MB` | `0` (tanpa batas) | Batas ukuran upload dalam MB; berlaku di UI dan server. Disarankan diisi di mode server agar disk tidak penuh |
| `DIARIZATION_THRESHOLD` | `1.2` | Batas kemiripan suara saat jumlah pembicara *Otomatis*; lebih kecil = lebih banyak pembicara |
| `WHISPER_WINDOWS_URL` / `WHISPER_WINDOWS_SHA256` | GitHub Release project ini | Sumber unduhan binary whisper Windows untuk setup otomatis |

Contoh: Linux `WHISPER_GPU_DEVICE=0 bash scripts/start_app.sh`; Windows CMD `set WHISPER_GPU_DEVICE=0` lalu jalankan script; PowerShell `$env:WHISPER_GPU_DEVICE="0"`.

**Nomor GPU:** biasanya tidak perlu diatur (`auto`). Untuk memaksa GPU tertentu, lihat daftarnya dengan menjalankan whisper-cli sekali dan cari baris `ggml_vulkan: 0 = ...`, `ggml_vulkan: 1 = ...`.

## Speaker diarization (bedakan pembicara)

Whisper hanya mengubah suara menjadi teks; ia tidak tahu siapa yang berbicara. Fitur **Bedakan pembicara** memberi label `Pembicara 1`, `Pembicara 2`, dst. pada setiap segmen.

**Langsung aktif, tanpa login atau token.** Library dan modelnya ikut [setup otomatis](#setup-otomatis-saat-pertama-dijalankan):

| Komponen | Ukuran | Sumber |
|---|---|---|
| Library [`sherpa-onnx`](https://github.com/k2-fsa/sherpa-onnx) (Apache-2.0) | ±11 MB (Linux) / ±17 MB (Windows) | PyPI, lewat `requirements/base.txt` |
| `models/pyannote-segmentation-3.0.onnx`: memotong audio per giliran bicara (PyAnnote segmentation-3.0, MIT) | 6 MB | GitHub Release sherpa-onnx |
| `models/nemo_en_titanet_small.onnx`: mengenali kemiripan suara (NVIDIA NeMo TitaNet-small) | 40 MB | GitHub Release sherpa-onnx |

Model PyAnnote resmi di Hugging Face mewajibkan login. sherpa-onnx membagikan versi ONNX-nya di GitHub, jadi tidak perlu akun, token, maupun PyTorch.

**Cara pakai:**
1. Centang **Bedakan pembicara**.
2. Pilih **Jumlah pembicara**: *Otomatis (ditebak)*, atau angka 2–10 jika jumlah orangnya diketahui (**disarankan**, hasilnya lebih andal).
3. Klik **Mulai Transkripsi**.

**Yang perlu diketahui:**
- **Tebakan otomatis bisa meleset.** Jumlah pembicara ditebak dari kemiripan suara, dan hasilnya sensitif. Pada rapat uji 10 menit, sedikit perubahan batas kemiripan mengubah hasil dari 1 menjadi 3 atau 7 orang. Bila tahu jumlahnya, isi angkanya. Batas bawaan (`DIARIZATION_THRESHOLD=1.2`) bisa diubah: lebih kecil = lebih banyak pembicara.
- **Berjalan di CPU**, setelah transkripsi selesai. Waktu tambahan ±5 detik per menit audio (rapat 56 menit: +4,6 menit, diukur di laptop dengan CPU 8 thread).
- **Label anonim**, bukan nama asli. Nomor diberikan sesuai urutan orang pertama kali bicara.
- Hasil terbaik pada rekaman yang jelas. Suara yang saling tumpang tindih, mikrofon jauh, atau dua orang dengan suara sangat mirip bisa tertukar.

Hasil uji (rekaman rapat bahasa Indonesia diselingi pidato bahasa Inggris, 3 menit): semua 22 segmen rapat → *Pembicara 1*, semua 16 segmen pidato → *Pembicara 2*, baik mode otomatis maupun jumlah = 2.

## Membuat paket siap pakai

Dijalankan di Linux, menghasilkan paket untuk kedua OS:

```bash
bash scripts/build_whisper.sh     # sekali, untuk binary Linux
bash scripts/package.sh           # atau: linux | windows
```

Hasil di `dist/`:

| File | Isi |
|---|---|
| `AudioTranscrypt-windows.zip` (~650 MB) | Python 3.12 portable, library Windows, `whisper-cli.exe` + runtime Visual C++, model turbo + VAD + model pembicara, `start.bat` |
| `AudioTranscrypt-linux.tar.gz` (~670 MB) | Python 3.12 portable, library Linux, `whisper-cli` Vulkan, model turbo + VAD + model pembicara, `start.sh` |

Syarat: semua model sudah ada di `models/` (jalankan `python3 -m app.bootstrap` dulu), plus `curl`, `zip`, dan `unzip`.

Target `windows` juga menghasilkan `dist/whisper-vulkan-windows-x64.zip` (±19 MB): binary whisper Windows yang diunduh oleh [setup otomatis](#setup-otomatis-saat-pertama-dijalankan).

Paket berisi **salinan** `app/` dan `static/` saat dibuat. Setiap ada perubahan kode, jalankan ulang `package.sh`, karena paket lama tidak ikut ter-update.

### Merilis binary Windows untuk setup otomatis (maintainer)

Pengguna Windows yang clone dari git mengunduh binary whisper dari GitHub Release, bukan dari repository. Langkahnya (sekali, dan setiap kali binary whisper berubah):

1. Buat rilis di https://github.com/theCrudify/01.-Audio-Transcrypt/releases/new dengan tag **`whisper-vulkan-bd9985c`**.
2. Upload `dist/whisper-vulkan-windows-x64.zip` sebagai asset rilis, lalu publish.
3. Repository harus **public**. Dari repo private, unduhan tanpa login akan gagal (404).
4. Jika zip dibuat ulang, sha256-nya berubah. Perbarui `WINDOWS_BINARY_SHA256` (dan tag di `WINDOWS_BINARY_URL` jika versi whisper berubah) di `app/bootstrap.py` dengan nilai yang dicetak `package.sh`.

Tanpa rilis ini, setup di Windows berhenti dengan pesan untuk menyalin folder `build-vulkan\` dari paket siap pakai. Lokasi lain bisa dipakai lewat env `WHISPER_WINDOWS_URL` + `WHISPER_WINDOWS_SHA256`.

## API

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/health` | Status backend, model, GPU, diarization |
| POST | `/api/warmup` | Cek kesiapan backend |
| POST | `/api/extract-audio` | Form `file` → unduhan WAV |
| POST | `/api/transcribe` | Form: `file`, `language` (kode Whisper mis. `id`/`en`/`ja`, atau `auto`), `task` (`transcribe`/`translate`), `beam_size` (1–8, batas whisper.cpp), `vad_filter`, `diarize`, `num_speakers` (0 = otomatis, 1–20). Respons berisi `language_checks`: daftar `{at, language, probability}` hasil cek bahasa di awal/tengah/akhir ucapan (kosong jika `language=auto`) |

Contoh:

```bash
curl -F file=@rapat.mp3 -F language=id http://127.0.0.1:8000/api/transcribe
```

## Struktur project

```text
app/
  config.py          Konfigurasi, path, environment variable
  main.py            FastAPI app & entrypoint (python -m app.main)
  transcriber.py     Menjalankan whisper-cli, fallback GPU/CPU, antrean GPU
  audio.py           Konversi audio/video ke WAV 16 kHz (PyAV, tanpa FFmpeg)
  diarization.py     Bedakan pembicara (sherpa-onnx, CPU, tanpa login)
  verify.py          Cek dependensi, binary, dan model
  bootstrap.py       Setup otomatis: .venv, whisper-cli, model (hanya library standar)
static/              Frontend (index.html)
tests/               Unit test (python -m unittest discover tests)
requirements/
  base.txt           Dependensi utama
scripts/
  start_app.bat      Launcher Windows (menjalankan setup otomatis dulu)
  start_app.sh       Launcher Linux / Git Bash (menjalankan setup otomatis dulu)
  build_whisper.sh   Build whisper.cpp Vulkan untuk Linux
  package.sh         Membuat paket siap pakai di dist/
build-vulkan/        whisper.cpp prebuilt Windows   (tidak di-commit)
build-linux/         whisper.cpp build Linux         (tidak di-commit)
models/              Model whisper & VAD             (tidak di-commit)
third_party/         Source whisper.cpp              (tidak di-commit)
uploads/             File sementara saat diproses    (tidak di-commit)
dist/                Hasil package.sh                (tidak di-commit)
```

## Cakupan & batasan

Bagian ini menjelaskan apa yang memang ditangani aplikasi, apa yang tidak, dan batasan teknis yang perlu diketahui sebelum dipakai untuk pekerjaan penting.

### Termasuk cakupan

- **Transkripsi file rekaman** audio/video menjadi teks bertimestamp, berjalan sepenuhnya di komputer sendiri.
- **Fokus bahasa Indonesia & Inggris**, termasuk bahasa Indonesia yang bercampur istilah Inggris. ±100 bahasa lain tersedia lewat pencarian, dengan kualitas yang berbeda-beda per bahasa.
- **Terjemahan langsung ke bahasa Inggris.**
- **Ekspor TXT & SRT**, salin teks, dan klik timestamp untuk memutar bagian itu.
- **Pemakaian pribadi** di satu komputer, atau **server LAN tepercaya** untuk tim kecil.
- **Privasi:** file upload dan WAV sementara dihapus setelah diproses; hasil transkrip hanya ada di browser pengguna, tidak disimpan di server.
- **UI ID/EN**, responsif untuk HP, tablet, dan laptop, dengan tema terang/gelap.

### Di luar cakupan (tidak didukung)

| Tidak didukung | Keterangan / alternatif |
|---|---|
| Transkripsi real-time (live) | Rekaman mikrofon baru diproses setelah perekaman dihentikan. |
| Terjemahan ke selain bahasa Inggris | Batasan Whisper. Misalnya Inggris → Indonesia tidak bisa. |
| Ganti bahasa otomatis per kalimat | Satu bahasa dikunci per file (lihat [catatan bahasa](#catatan-cara-kerja-pilihan-bahasa)). Potong file per bagian bahasa. |
| Nama asli pembicara | *Bedakan pembicara* hanya memberi label anonim *Pembicara 1, 2, …*. |
| Riwayat hasil | Hasil hilang saat halaman di-refresh atau ditutup. Unduh TXT/SRT dulu. |
| Edit teks, ringkasan otomatis, ekspor DOCX/PDF | Salin atau unduh TXT, lalu olah di aplikasi lain. |
| Login, hak akses, HTTPS | Siapa pun di jaringan bisa memakai server. Jangan buka ke internet. |
| Membatalkan transkripsi yang sedang berjalan | Lihat *Batal / tutup halaman* di bawah. |

### Batasan teknis

| Area | Batasan | Dampak / yang bisa dilakukan |
|---|---|---|
| Akurasi | Whisper bisa salah menulis nama orang, istilah teknis, singkatan, dan angka. Pada bagian hening/musik kadang muncul teks "halusinasi". | Biarkan VAD aktif dan periksa ulang hasil untuk dokumen penting. |
| Pilihan bahasa | Satu bahasa dikunci untuk seluruh file. | Pilih bahasa mayoritas; bagian panjang berbahasa lain sebaiknya ditranskrip terpisah. |
| Deteksi otomatis | Hanya menilai 30 detik pertama. | Pilih bahasa secara manual jika diketahui. |
| Cek bahasa | Hanya 3 titik sampel (awal/tengah/akhir), menambah ±4 detik. | Perpindahan bahasa singkat di antara titik itu tidak terdeteksi. |
| Bahasa daerah | Jawa dan Sunda jauh lebih lemah dari Indonesia/Inggris karena data latih Whisper sedikit. | Hasil lebih andal bila memilih *Indonesia*; peningkatan nyata butuh model yang di-fine-tune. |
| Ketelitian (beam) | Maksimal 8 (batas whisper.cpp `WHISPER_MAX_DECODERS`). | Di atas 5 peningkatannya sangat kecil tapi lebih lambat. |
| Antrean | Hanya satu transkripsi berjalan di GPU pada satu waktu; posisi antrean tidak ditampilkan. | Di mode server, pengguna lain melihat timer berjalan lebih lama sampai gilirannya. |
| Progres | Persentase hanya untuk upload; transkripsi hanya menampilkan waktu berjalan. | Perkiraan: ±3 menit per jam audio di GPU RX 6500M; di CPU ±1,5× durasi audio. |
| Batal / tutup halaman | Menutup atau me-refresh halaman **tidak** menghentikan proses di server; GPU tetap terpakai sampai selesai, dan hasilnya hilang. | Tunggu sampai selesai; aplikasi memberi peringatan saat halaman akan ditutup. |
| Waktu maksimal | `WHISPER_TIMEOUT_SECONDS` = 1 jam per file. File sangat panjang di CPU bisa melewatinya. | Naikkan nilainya atau pakai GPU. |
| Ukuran file | Default tanpa batas. Selama diproses, server butuh ruang disk untuk file asli + WAV sementara (±115 MB per jam audio). | Di mode server, isi `MAX_UPLOAD_MB`. |
| Gagal di GPU | Jika whisper gagal, aplikasi mencoba ulang di GPU 0 lalu CPU, termasuk untuk kegagalan yang tidak terkait GPU. | Pesan error bisa muncul lebih lama dari seharusnya. |
| Rekam mikrofon | Hanya bisa di `localhost`/`127.0.0.1` atau HTTPS (aturan browser). | Pengguna mode server lewat `http://<IP>` bisa mengunggah file rekaman. |
| Bahasa pesan error | Pesan error dari server selalu berbahasa Indonesia, walau UI diset ke EN. | – |
| Bedakan pembicara | Jumlah pembicara *Otomatis* bisa meleset (sensitif); berjalan di CPU (±5 menit per jam audio); suara tumpang tindih/mirip bisa tertukar. | Isi *Jumlah pembicara* jika diketahui. Lihat [Speaker diarization](#speaker-diarization-bedakan-pembicara). |
| Setup pertama | Butuh internet dan ±600 MB unduhan. Linux butuh tool build (git, cmake, compiler, glslc); Windows butuh rilis binary di GitHub Release. | Setelah itu aplikasi berjalan offline. Alternatif tanpa setup: paket siap pakai. |
| Paket siap pakai | Berisi salinan kode saat paket dibuat. | Jalankan ulang `scripts/package.sh` setelah kode berubah. |

## Troubleshooting

**`[setup] GAGAL: ...` saat pertama dijalankan**
Pesan di bawahnya menyebutkan penyebab dan perbaikannya. Yang umum:
- *Gagal mengunduh*: cek koneksi internet, lalu jalankan ulang (unduhan yang terputus tidak dipakai).
- *Tool berikut belum terpasang* (Linux): jalankan perintah `sudo apt install ...` yang ditampilkan.
- *Butuh python3-venv* (Linux): `sudo apt install python3-venv`.
- *Binary Windows 404*: rilis GitHub belum dibuat atau repo masih private (lihat [Merilis binary Windows](#merilis-binary-windows-untuk-setup-otomatis-maintainer)). Sementara itu, salin folder `build-vulkan\` dari paket siap pakai.

**Status tidak pernah "Siap" / `503 Service Unavailable`**
Jalankan `.venv/bin/python -m app.verify` (Windows: `.venv\Scripts\python -m app.verify`) untuk melihat file mana yang hilang (binary whisper atau model).

**`whisper.cpp gagal (exit ...)`**
Pesan error menampilkan log whisper. Penyebab umum:
- VRAM tidak cukup — tutup aplikasi lain yang memakai GPU, atau paksa GPU lain dengan `WHISPER_GPU_DEVICE=0`.
- Driver Vulkan tidak ada — Linux: `sudo apt install mesa-vulkan-drivers`; Windows: update driver GPU. Aplikasi seharusnya otomatis pindah ke CPU.

**Hasil mengulang kalimat yang sama terus-menerus**
Pastikan memakai versi terbaru (`-mc 0` aktif) dan model turbo.

**Banyak teks aneh di bagian hening**
Pastikan `models/ggml-silero-v5.1.2.bin` ada dan opsi VAD dicentang.

**Transkripsi lambat**
Kemungkinan berjalan di CPU. Cek dengan menjalankan whisper-cli langsung, misalnya di Linux:
```bash
build-linux/bin/whisper-cli -m models/ggml-large-v3-turbo-q5_0.bin -f contoh.wav -dev 1 2>&1 | grep -i vulkan
```
Baris `using Vulkan1 backend` berarti GPU dipakai. Jika tidak ada, cek driver Vulkan dan `WHISPER_GPU_DEVICE`.

**Linux: `GLIBC_2.38 not found` saat memakai paket**
Distro terlalu lama untuk paket Linux; jalankan dari source (Cara 2) agar whisper.cpp di-build di mesin itu.

**Windows: `python` tidak dikenali**
Install Python dari python.org dan centang *Add python.exe to PATH*, atau pakai paket siap pakai yang tidak butuh Python.

**Port 8000 sudah dipakai**
Aplikasi otomatis memakai port berikutnya (8001, 8002, …); lihat alamat yang dicetak di terminal.

**`too many decoders requested (10), max = 8` / `Beam size harus berada di antara 1 dan 8`**
Halaman lama masih tersimpan di browser (dulu slider beam sampai 10). Refresh dengan Ctrl+F5; slider sekarang maksimal 8.

**`Kode bahasa tidak dikenal`**
Hanya terjadi lewat API: isi `language` dengan `auto` atau kode Whisper (`id`, `en`, `ja`, `jw` untuk Jawa, `su` untuk Sunda, dst.). Daftar lengkapnya ada di `WHISPER_LANGUAGES` pada `app/config.py`.

**Muncul peringatan bahasa padahal pilihan sudah benar**
Peringatan berdasarkan 3 sampel 30 detik, jadi bisa keliru pada bagian yang didominasi istilah asing, musik, atau suara latar. Jika hasil transkrip terlihat baik, klik **Abaikan**.

**Tampilan aneh / fitur baru tidak muncul setelah update**
Refresh browser dengan Ctrl+F5 agar memakai halaman terbaru.
