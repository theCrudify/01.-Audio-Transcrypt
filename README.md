# Local AI Transcription Studio

Aplikasi transkripsi audio dan video lokal. Pemrosesan berjalan di komputer sendiri menggunakan `whisper.cpp` dengan Vulkan, sehingga GPU AMD seperti Radeon RX 6550M dapat digunakan.

## Fitur

- Upload audio/video melalui browser.
- Pisahkan (ekstrak) audio dari file video menjadi file WAV yang bisa diunduh, sebelum ditranskrip.
- Transkripsi bahasa Indonesia, Inggris, Melayu, Jawa, atau deteksi otomatis.
- Mode transkripsi dan terjemahan ke bahasa Inggris.
- Timestamp setiap bagian hasil.
- Salin atau unduh hasil sebagai TXT.
- Backend GPU Vulkan dengan fallback error yang jelas.
- Opsi speaker diarization melalui PyAnnote.

## Struktur penting

```text
app/                           Modul backend aplikasi
  ├── config.py                Konfigurasi aplikasi & path
  ├── main.py                  Entrypoint FastAPI backend
  └── verify.py                Script verifikasi setup & GPU
requirements/                  Daftar dependensi Python
  ├── base.txt                 Dependensi utama
  └── diarization.txt          Dependensi opsional speaker diarization
scripts/                       Script launcher aplikasi
  ├── start_app.bat            Launcher Windows (bisa diklik langsung dari folder scripts/)
  └── start_app.sh             Launcher Bash
static/                        Tampilan web frontend
  └── index.html
build-vulkan/bin/Release/      whisper.cpp Vulkan
models/ggml-small.bin          Model Whisper
uploads/                       File sementara saat diproses
README.md                      Dokumentasi proyek
.gitignore                     Daftar abaikan git
```

Folder `build-vulkan/`, `models/`, `third_party/`, `uploads/`, cache Python, dan file log tidak perlu diubah atau dimasukkan ke repository.

## Cara menjalankan di Windows

### 1. Buka terminal di folder project

Buka folder project berikut di File Explorer:

```text
D:\01. Projekan Freelance\01. Audio Transcrypt
```

Klik address bar, ketik `cmd`, lalu tekan Enter.

### 2. Install dependensi Python

Jalankan sekali:

```bat
python -m pip install -r requirements/base.txt
```

Jika `python` tidak dikenali, gunakan Anaconda Prompt atau aktifkan environment Python yang biasa dipakai.

### 3. Cek instalasi GPU

```bat
python -m app.verify
```

Output terakhir harus berbunyi:

```text
Ready to run with AMD Vulkan GPU.
```

### 4. Jalankan aplikasi

Cara yang disarankan (melalui script launcher):

```bat
scripts\start_app.bat
```
*(atau langsung buka folder `scripts/` dan double-click `start_app.bat`)*

Jika menggunakan Git Bash:

```bash
bash scripts/start_app.sh
```

Atau langsung via Python:

```bat
python -m app.main
```

### 5. Buka web

Buka alamat berikut di browser:

```text
http://127.0.0.1:8000
```

Tunggu badge status berubah menjadi `Siap`. Jangan menutup terminal selama aplikasi digunakan.

## Verifikasi GPU

Buka:

```text
http://127.0.0.1:8000/health
```

Konfigurasi yang benar terlihat seperti ini:

```json
{
  "backend": "whisper.cpp Vulkan",
  "device": "vulkan",
  "gpu_device": 1
}
```

Pada laptop ini, `GPU1` adalah Radeon RX 6550M dan `GPU0` adalah iGPU AMD.

## Konfigurasi opsional

PowerShell:

```powershell
$env:WHISPER_GPU_DEVICE="1"
$env:WHISPER_MODEL_PATH="models\ggml-small.bin"
$env:WHISPER_CLI="build-vulkan\bin\Release\whisper-cli.exe"
$env:MAX_UPLOAD_MB="512"
python app.py
```

Model `small` cukup akurat dan masih sesuai untuk GPU 4 GB. Model lebih besar membutuhkan ruang dan VRAM lebih banyak.

## Memisahkan audio dari video

Jika kamu punya file video dan ingin mengambil audionya terlebih dahulu sebelum membuat transkrip:

1. Pilih file video pada area upload.
2. Klik tombol `Pisahkan Audio dari Video`.
3. Server akan mengekstrak jalur audio dari video tersebut dan menyimpannya sebagai file `.wav` yang otomatis terunduh ke komputer kamu.
4. File audio hasil ekstraksi tersebut langsung menggantikan file yang dipilih, jadi kamu tinggal klik `Mulai Transkripsi` untuk membuat transkripnya.

Catatan: Fitur `Mulai Transkripsi` sebenarnya sudah bisa memproses video secara langsung tanpa langkah ini (audio diekstrak otomatis di balik layar). Tombol `Pisahkan Audio dari Video` berguna kalau kamu ingin menyimpan salinan audionya secara terpisah, atau memproses audio itu di aplikasi lain.

## Speaker diarization (opsional)

Whisper mengenali isi ucapan, bukan identitas suara. Untuk memberi label `Pembicara 1`, `Pembicara 2`, dan seterusnya, pasang pipeline diarization:

```bat
python -m pip install -r requirements-diarization.txt
```

Buat token baca dari Hugging Face, terima akses model `pyannote/speaker-diarization-3.1`, lalu buka terminal baru:

```powershell
$env:HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"
start_app.bat
```

Setelah status server siap, centang `Bedakan pembicara`. Hasil akan diberi label berdasarkan karakteristik suara, tetapi labelnya tetap anonim (`Pembicara 1`, `Pembicara 2`), bukan nama asli. Untuk mengetahui nama orang, diperlukan sampel suara referensi dan proses voice identification tambahan.

## Speaker diarization

Whisper hanya mengubah suara menjadi teks; ia tidak mengetahui siapa yang berbicara. Untuk memberi label `SPEAKER_00`, `SPEAKER_01`, dan seterusnya:

1. Buat token Hugging Face dan terima akses model `pyannote/speaker-diarization-3.1` serta model dependensinya di halaman Hugging Face.
2. Install dependensi tambahan:

```bat
python -m pip install -r requirements-diarization.txt
```

3. Atur token hanya untuk sesi terminal saat ini:

```powershell
$env:HF_TOKEN="hf_token_kamu"
python app.py
```

4. Aktifkan opsi `Bedakan pembicara` sebelum memproses file.

Tanpa token atau dependensi tambahan, aplikasi tetap dapat membuat transkrip biasa, tetapi tidak akan mengarang label pembicara.

## Troubleshooting

### `503 Service Unavailable`

Pastikan `build-vulkan/bin/Release/whisper-cli.exe` dan `models/ggml-small.bin` ada. Jalankan:

```bat
python verify_setup.py
```

Tutup server lama dengan `Ctrl+C`, kemudian jalankan `start_app.bat` lagi.

### `No such file or directory`

Jangan menjalankan `app.py` dari folder lain. Jalankan `start_app.bat` dari folder project. File upload diproses sementara di folder `uploads/`.

### Checkbox speaker tidak aktif

Itu berarti `pyannote.audio` atau `HF_TOKEN` belum tersedia. Transkripsi biasa tetap bisa digunakan tanpa diarization.

### Port 8000 sedang digunakan

Tutup terminal yang menjalankan aplikasi lama, lalu jalankan kembali `start_app.bat`. Jika perlu, gunakan:

```powershell
$env:PORT="8001"
python app.py
```

Kemudian buka `http://127.0.0.1:8001`.

### Transkripsi video panjang

Durasi proses bergantung pada panjang video dan penggunaan GPU. Biarkan halaman tetap terbuka sampai proses selesai.

## Catatan

Label `Pembicara 1` atau nama orang belum tersedia. Fitur tersebut memerlukan speaker diarization dan pengenalan suara tambahan.
