# Local AI Transcription Studio

Aplikasi web untuk mentranskrip audio dan video **sepenuhnya di komputer sendiri** (tanpa cloud), memakai [whisper.cpp](https://github.com/ggerganov/whisper.cpp) dengan akselerasi GPU Vulkan. Berjalan di **Windows dan Linux**, di laptop pribadi maupun sebagai server untuk satu tim.

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
10. [Speaker diarization (opsional)](#speaker-diarization-opsional)
11. [Membuat paket siap pakai](#membuat-paket-siap-pakai)
12. [API](#api)
13. [Struktur project](#struktur-project)
14. [Troubleshooting](#troubleshooting)

## Fitur

- Upload audio/video lewat browser: `aac, flac, m4a, mkv, mov, mp3, mp4, ogg, opus, wav, webm` (maks. 512 MB, bisa diubah).
- Bahasa: Indonesia, Inggris, Melayu, Jawa, atau deteksi otomatis.
- Mode transkripsi, atau terjemahan langsung ke bahasa Inggris.
- Timestamp per segmen; salin atau unduh hasil sebagai TXT.
- Ekstrak audio dari video menjadi file WAV.
- GPU Vulkan (AMD, NVIDIA, Intel). Jika GPU gagal, otomatis pindah ke GPU lain lalu ke CPU.
- VAD (Voice Activity Detection) untuk melewati bagian hening dan mengurangi teks "halusinasi".
- Opsional: label pembicara (speaker diarization) via PyAnnote.
- Tidak butuh Anaconda, FFmpeg, atau koneksi internet saat dipakai.

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

### Prasyarat

| | Windows | Linux |
|---|---|---|
| Python | 3.10+ dari [python.org](https://www.python.org/downloads/) (centang *Add python.exe to PATH*). Anaconda juga bisa, tapi **tidak wajib**. | `python3` + `python3-venv` |
| whisper.cpp | Sudah tersedia di `build-vulkan/bin/Release/` | Di-build sekali (lihat di bawah) |
| Model | Unduh ke `models/` (lihat [Model](#model--kualitas-transkripsi)) | sama |

### Windows

```bat
cd "path\ke\project"
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements\base.txt
scripts\start_app.bat
```

`start_app.bat` otomatis memakai `.venv` jika ada, lalu `python`, lalu `py`. Script ini juga bisa langsung di-double-click dari folder `scripts\`.

### Linux

```bash
# 1. Paket build (Debian/Ubuntu)
sudo apt install build-essential cmake libvulkan-dev glslc mesa-vulkan-drivers python3-venv

# 2. Build whisper.cpp dengan Vulkan ke build-linux/
bash scripts/build_whisper.sh

# 3. Dependensi Python
python3 -m venv .venv
.venv/bin/pip install -r requirements/base.txt

# 4. Jalankan
bash scripts/start_app.sh
```

Lalu buka http://127.0.0.1:8000. Saat dijalankan dari source, server otomatis restart setiap kali kode berubah (`APP_RELOAD=1`).

### Cek setup

```bash
python -m app.verify
```

Output terakhir harus `Ready to run (Vulkan GPU, CPU fallback).`

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

1. Tunggu badge status berubah menjadi **Siap**.
2. Pilih atau drag-and-drop file audio/video.
3. Atur opsi:
   - **Bahasa**: pilih bahasa yang diucapkan. Memilih bahasa yang tepat lebih akurat daripada *Auto Detect*.
   - **Mode**: *Transkripsi* (bahasa asli) atau *Terjemahkan* (ke Inggris).
   - **Beam (1–10)**: 5 adalah keseimbangan terbaik; lebih besar sedikit lebih akurat tapi lebih lambat.
   - **VAD**: biarkan aktif; melewati bagian hening.
   - **Bedakan pembicara**: hanya muncul jika diarization dipasang.
4. Klik **Mulai Transkripsi**. File 1 jam ±3 menit di GPU RX 6500M.
5. Salin atau unduh hasil sebagai TXT.

**Pisahkan Audio dari Video**: mengekstrak audio video menjadi WAV yang terunduh otomatis dan menggantikan file yang dipilih. Ini opsional — *Mulai Transkripsi* bisa langsung memproses video.

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

Linux, unduh sekaligus:

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
| `MAX_UPLOAD_MB` | `512` | Batas ukuran upload |
| `HF_TOKEN` | – | Token Hugging Face untuk diarization |

Contoh: Linux `WHISPER_GPU_DEVICE=0 bash scripts/start_app.sh`; Windows CMD `set WHISPER_GPU_DEVICE=0` lalu jalankan script; PowerShell `$env:WHISPER_GPU_DEVICE="0"`.

**Nomor GPU:** biasanya tidak perlu diatur (`auto`). Untuk memaksa GPU tertentu, lihat daftarnya dengan menjalankan whisper-cli sekali dan cari baris `ggml_vulkan: 0 = ...`, `ggml_vulkan: 1 = ...`.

## Speaker diarization (opsional)

Whisper hanya mengubah suara menjadi teks; ia tidak tahu siapa yang berbicara. Untuk label `Pembicara 1`, `Pembicara 2`, dst.:

1. Buat token *read* di Hugging Face dan terima syarat akses model `pyannote/speaker-diarization-3.1` beserta model dependensinya.
2. Install dependensi tambahan (±2 GB, termasuk PyTorch):
   ```bash
   pip install -r requirements/diarization.txt
   ```
3. Set token lalu jalankan aplikasi:
   ```bash
   HF_TOKEN=hf_xxx bash scripts/start_app.sh          # Linux
   ```
   ```bat
   set HF_TOKEN=hf_xxx
   scripts\start_app.bat
   ```
4. Centang **Bedakan pembicara** sebelum memproses.

Label tetap anonim, bukan nama asli. Diarization tidak termasuk dalam paket siap pakai.

## Membuat paket siap pakai

Dijalankan di Linux, menghasilkan paket untuk kedua OS:

```bash
bash scripts/build_whisper.sh     # sekali, untuk binary Linux
bash scripts/package.sh           # atau: linux | windows
```

Hasil di `dist/`:

| File | Isi |
|---|---|
| `AudioTranscrypt-windows.zip` (~650 MB) | Python 3.12 portable, library Windows, `whisper-cli.exe` + runtime Visual C++, model turbo + VAD, `start.bat` |
| `AudioTranscrypt-linux.tar.gz` (~670 MB) | Python 3.12 portable, library Linux, `whisper-cli` Vulkan, model turbo + VAD, `start.sh` |

Syarat: model turbo dan VAD sudah ada di `models/`, plus `curl`, `zip`, dan `unzip`.

## API

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/health` | Status backend, model, GPU, diarization |
| POST | `/api/warmup` | Cek kesiapan backend |
| POST | `/api/extract-audio` | Form `file` → unduhan WAV |
| POST | `/api/transcribe` | Form: `file`, `language` (`id`/`en`/`ms`/`jw`/`auto`), `task` (`transcribe`/`translate`), `beam_size` (1–10), `vad_filter`, `diarize` |

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
  diarization.py     Speaker diarization (PyAnnote, opsional)
  verify.py          Cek dependensi, binary, dan model
static/              Frontend (index.html)
requirements/
  base.txt           Dependensi utama
  diarization.txt    Dependensi diarization (opsional)
scripts/
  start_app.bat      Launcher Windows
  start_app.sh       Launcher Linux / Git Bash
  build_whisper.sh   Build whisper.cpp Vulkan untuk Linux
  package.sh         Membuat paket siap pakai di dist/
build-vulkan/        whisper.cpp prebuilt Windows   (tidak di-commit)
build-linux/         whisper.cpp build Linux         (tidak di-commit)
models/              Model whisper & VAD             (tidak di-commit)
third_party/         Source whisper.cpp              (tidak di-commit)
uploads/             File sementara saat diproses    (tidak di-commit)
dist/                Hasil package.sh                (tidak di-commit)
```

## Troubleshooting

**Status tidak pernah "Siap" / `503 Service Unavailable`**
Jalankan `python -m app.verify` untuk melihat file mana yang hilang (binary whisper atau model).

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

**Pilihan bahasa Jawa tidak berpengaruh / error**
Refresh browser dengan Ctrl+F5 agar memakai halaman terbaru (kode bahasa `jw`).
