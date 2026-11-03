# Komponen pihak ketiga & lisensinya

Kode project ini sendiri berlisensi MIT (lihat [LICENSE](LICENSE)). Komponen di bawah ini milik pembuatnya masing-masing.

Aplikasi ini merangkai komponen open-source buatan pihak lain. Repository ini **tidak** menyimpan model atau binary mereka; semuanya diunduh dari sumber resminya saat [setup otomatis](README.md#yang-disiapkan-otomatis), dan tunduk pada lisensinya masing-masing. Satu-satunya yang disebarkan ulang adalah zip binary whisper.cpp untuk Windows di GitHub Release, dan teks lisensinya ikut disertakan di dalam zip itu.

Terima kasih kepada semua pembuatnya.

## Model AI

| Komponen | Pembuat | Lisensi | Sumber | Dipakai untuk |
|---|---|---|---|---|
| Whisper large-v3-turbo | OpenAI | MIT | [openai/whisper](https://github.com/openai/whisper) | Speech-to-text |
| Model Whisper format ggml (`ggml-large-v3-turbo-q5_0.bin`) | ggml / whisper.cpp | MIT | [ggerganov/whisper.cpp](https://huggingface.co/ggerganov/whisper.cpp) | Speech-to-text di whisper.cpp |
| Silero VAD v5.1.2 (format ggml) | Silero Team | MIT | [snakers4/silero-vad](https://github.com/snakers4/silero-vad), [ggml-org/whisper-vad](https://huggingface.co/ggml-org/whisper-vad) | Melewati bagian hening |
| PyAnnote segmentation-3.0 (ONNX) | CNRS / pyannote (Hervé Bredin, Alexis Plaquet) | MIT, teks lisensi: `models/pyannote-segmentation-3.0.LICENSE.txt` | [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0), versi ONNX dari [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx/releases/tag/speaker-segmentation-models) | Memotong audio per giliran bicara |
| 3D-Speaker ERes2Net, VoxCeleb (ONNX) | 3D-Speaker, Alibaba (Tongyi Lab) | Apache-2.0 | [modelscope/3D-Speaker](https://github.com/modelscope/3D-Speaker), [iic/speech_eres2net_sv_en_voxceleb_16k](https://modelscope.cn/models/iic/speech_eres2net_sv_en_voxceleb_16k), versi ONNX dari [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx/releases/tag/speaker-recongition-models) | Mengenali kemiripan suara |

Mengutip PyAnnote (diminta oleh pembuatnya bila dipakai dalam publikasi):

> Plaquet, A., & Bredin, H. (2023). *Powerset multi-class cross entropy loss for neural speaker diarization.* Proc. INTERSPEECH 2023.
> Bredin, H. (2023). *pyannote.audio 2.1 speaker diarization pipeline: principle, benchmark, and recipe.* Proc. INTERSPEECH 2023.

## Mesin & library

| Komponen | Lisensi | Sumber | Catatan |
|---|---|---|---|
| whisper.cpp / ggml (fork `lemonade-sdk/whisper.cpp-amd`, commit `bd9985c`) | MIT | [lemonade-sdk/whisper.cpp-amd](https://github.com/lemonade-sdk/whisper.cpp-amd) | Di-build dari source (Linux) atau binary di GitHub Release (Windows). Teks lisensi: `LICENSE-whisper.cpp.txt` di dalam zip |
| sherpa-onnx | Apache-2.0 | [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | Termasuk ONNX Runtime (MIT, Microsoft) |
| FastAPI | MIT | [fastapi/fastapi](https://github.com/fastapi/fastapi) | |
| Uvicorn | BSD-3-Clause | [encode/uvicorn](https://github.com/encode/uvicorn) | |
| python-multipart | Apache-2.0 | [Kludex/python-multipart](https://github.com/Kludex/python-multipart) | |
| NumPy | BSD-3-Clause (+ komponen 0BSD, MIT, Zlib, CC0) | [numpy/numpy](https://github.com/numpy/numpy) | |
| PyAV | BSD-3-Clause | [PyAV-Org/PyAV](https://github.com/PyAV-Org/PyAV) | Wheel PyAV membawa **FFmpeg (LGPL-3.0+)** serta **libx264 & libx265 (GPL-2.0+)**. Aplikasi hanya memakai fungsi decode audio. Wheel ini diunduh `pip` dari PyPI saat setup; repository ini tidak menyebarkannya. Source code-nya tersedia di [FFmpeg](https://ffmpeg.org/download.html), [x264](https://code.videolan.org/videolan/x264), [x265](https://bitbucket.org/multicoreware/x265_git) dan build script PyAV. Teks lisensi tiap library ada di folder `*.dist-info` PyAV di dalam `.venv`. |
| Runtime Microsoft Visual C++ (zip whisper Windows) | Lisensi redistribusi Microsoft | wheel `msvc-runtime` | Disertakan agar `whisper-cli.exe` jalan tanpa installer |

## Merek dagang

Nama seperti OpenAI, Whisper, NVIDIA, AMD, Radeon, Alibaba, dan Microsoft adalah merek dagang pemiliknya masing-masing, disebut hanya untuk menjelaskan komponen atau perangkat keras yang dipakai. Project ini tidak berafiliasi dengan, atau didukung oleh, pemilik merek tersebut.
