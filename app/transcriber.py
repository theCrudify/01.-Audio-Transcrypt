import json
import os
import re
import subprocess
import threading
import wave
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from app.audio import convert_to_wav
from app.config import CLI_PATH, GPU_DEVICE, MODEL_PATH, TEMP_DIR, VAD_MODEL_PATH
from app.diarization import (
    diarization_available,
    dominant_speaker,
    label_for,
    parse_vad_map,
    segment_words,
    speaker_turns,
    split_by_speaker,
)

backend_error = None
# GPU 4 GB hanya muat satu proses whisper; request lain menunggu giliran.
gpu_lock = threading.Lock()


def backend_ready() -> bool:
    """Validates availability of whisper-cli executable and model file."""
    global backend_error
    if not CLI_PATH.is_file():
        backend_error = f"whisper-cli tidak ditemukan: {CLI_PATH}"
        return False
    if not MODEL_PATH.is_file():
        backend_error = f"Model ggml tidak ditemukan: {MODEL_PATH}"
        return False
    backend_error = None
    return True


def pick_gpu_device(whisper_log: str) -> int | None:
    """Nomor -dev untuk GPU diskrit pertama, lalu iGPU pertama; None jika tidak ada GPU (pakai CPU)."""
    found = re.findall(r"found GPU device \d+: .*\(type: (\d+), cnt: (\d+)\)", whisper_log)
    for wanted_type in ("1", "2"):  # GGML_BACKEND_DEVICE_TYPE_GPU, GGML_BACKEND_DEVICE_TYPE_IGPU
        for dev_type, cnt in found:
            if dev_type == wanted_type:
                return int(cnt)
    return None


@lru_cache(maxsize=1)
def gpu_device() -> int | None:
    if GPU_DEVICE != "auto":
        return int(GPU_DEVICE)
    # -dev 99 membuat whisper mencetak semua GPU; file kosong membuatnya berhenti setelah model dimuat (~1 detik).
    probe_path = TEMP_DIR / f"gpu-probe-{uuid4().hex}.wav"
    probe_path.touch()
    try:
        completed = subprocess.run(
            [str(CLI_PATH), "-m", str(MODEL_PATH), "-f", str(probe_path), "-dev", "99"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    finally:
        probe_path.unlink(missing_ok=True)
    return pick_gpu_device(completed.stderr + completed.stdout)


def parse_detected_language(whisper_log: str) -> tuple[str, float] | None:
    """Kode bahasa & probabilitas dari output `whisper-cli -dl`, atau None jika tidak ada."""
    match = re.search(r"auto-detected language: (\w+) \(p = ([\d.]+)\)", whisper_log)
    return (match.group(1), float(match.group(2))) if match else None


def _run_cli(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def detect_language(wav_path: Path, device_args: list[str]) -> tuple[str, float] | None:
    """Deteksi bahasa dari 30 detik pertama file (~1-2 detik). Hanya untuk peringatan, jadi kegagalan diabaikan."""
    try:
        completed = _run_cli(
            [str(CLI_PATH), "-m", str(MODEL_PATH), "-f", str(wav_path), "-l", "auto", "-dl", *device_args],
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_detected_language(completed.stderr + completed.stdout)


def pick_check_points(speech_starts: list[float], duration: float, min_gap: float = 60) -> list[float]:
    """Awal, tengah, dan akhir bagian yang berisi ucapan; titik yang berjarak < min_gap detik digabung."""
    points: list[float] = []
    if not speech_starts:
        return points
    for target in (0, duration / 2, max(0, duration - 60)):
        start = min(speech_starts, key=lambda s: abs(s - target))
        if all(abs(start - p) >= min_gap for p in points):
            points.append(start)
    return points


def slice_wav(source: Path, target: Path, start_s: float, seconds: float = 30) -> None:
    with wave.open(str(source), "rb") as src:
        rate = src.getframerate()
        src.setpos(min(src.getnframes(), int(start_s * rate)))
        frames = src.readframes(int(seconds * rate))
        with wave.open(str(target), "wb") as out:
            out.setparams(src.getparams())
            out.writeframes(frames)


def check_languages(wav_path: Path, speech_starts: list[float], duration: float, device_args: list[str]) -> list[dict]:
    """Deteksi bahasa di awal/tengah/akhir ucapan; whisper sendiri hanya menilai 30 detik pertama (-dl abaikan -ot)."""
    checks = []
    for at in pick_check_points(speech_starts, duration):
        clip = TEMP_DIR / f"lang-check-{uuid4().hex}.wav"
        try:
            slice_wav(wav_path, clip, at)
            found = detect_language(clip, device_args)
        except (OSError, wave.Error):
            found = None
        finally:
            clip.unlink(missing_ok=True)
        if found:
            checks.append({"at": round(at, 2), "language": found[0], "probability": round(found[1], 3)})
    return checks


def run_transcription(
    audio_path: Path,
    language_code: str | None,
    task: str,
    beam_size: int,
    vad_filter: bool,
    diarize: bool,
    num_speakers: int = 0,
):
    """Executes whisper.cpp Vulkan backend on GPU and processes segments."""
    if not backend_ready():
        raise RuntimeError(backend_error or "Backend Vulkan belum tersedia.")

    temp_id = uuid4().hex
    wav_path = TEMP_DIR / f"whisper-input-{temp_id}.wav"
    output_prefix = TEMP_DIR / f"whisper-result-{temp_id}"
    json_path = output_prefix.with_suffix(".json")
    try:
        convert_to_wav(audio_path, wav_path)

        if not wav_path.is_file() or wav_path.stat().st_size < 100:
            raise RuntimeError("Gagal menghasilkan file audio WAV yang valid untuk diproses.")

        base_command = [
            str(CLI_PATH),
            "-m", str(MODEL_PATH),
            "-f", str(wav_path),
            # JSON lengkap berisi waktu per token; dipakai untuk memotong kalimat di titik ganti pembicara.
            "-ojf" if diarize else "-oj",
            "-of", str(output_prefix),
            "-t", str(max(1, min(8, os.cpu_count() or 4))),
            "-bs", str(beam_size),
            "-l", language_code or "auto",
            # Tanpa konteks teks sebelumnya: mencegah loop kalimat berulang pada audio panjang.
            "-mc", "0",
            "-sns",
        ]
        if task == "translate":
            base_command.append("-tr")
        if vad_filter and VAD_MODEL_PATH.is_file():
            base_command += ["--vad", "-vm", str(VAD_MODEL_PATH), "-vsd", "500"]

        timeout = int(os.getenv("WHISPER_TIMEOUT_SECONDS", "3600"))
        with gpu_lock:
            device = gpu_device()
            device_args = ["-ng"] if device is None else ["-dev", str(device)]
            used_args = device_args
            completed = _run_cli(base_command + device_args, timeout)

            # Jika gagal pada GPU tertentu, coba GPU 0, lalu CPU (laptop/server tanpa GPU Vulkan)
            fallbacks = [["-dev", "0"]] if device not in (None, 0) else []
            for fallback_args in fallbacks + ([["-ng"]] if device is not None else []):
                if completed.returncode == 0:
                    break
                used_args = fallback_args
                completed = _run_cli(base_command + fallback_args, timeout)

        if completed.returncode != 0 or not json_path.is_file():
            details = (completed.stderr or completed.stdout or "").strip()[-1200:]
            raise RuntimeError(f"whisper.cpp gagal (exit {completed.returncode}): {details}")

        payload = json.loads(json_path.read_text(encoding="utf-8"))

        # Bahasa dipilih manual (dikunci untuk seluruh file): cek apakah ucapan di awal/tengah/akhir cocok,
        # agar UI bisa memperingatkan salah pilih atau rekaman campuran.
        language_checks = []
        if language_code:
            starts = [seg.get("offsets", {}).get("from", 0) / 1000 for seg in payload.get("transcription", []) if seg.get("text", "").strip()]
            ends = [seg.get("offsets", {}).get("to", 0) / 1000 for seg in payload.get("transcription", [])]
            with gpu_lock:
                language_checks = check_languages(wav_path, starts, max(ends, default=0), used_args)

        turns = None
        if diarize:
            if not diarization_available():
                raise RuntimeError("Diarization belum siap (model/sherpa-onnx belum ada). Jalankan: python -m app.bootstrap")
            turns = speaker_turns(wav_path, num_speakers)
    finally:
        for temp_file in [wav_path, *TEMP_DIR.glob(f"whisper-result-{temp_id}.*")]:
            temp_file.unlink(missing_ok=True)

    transcript_segments = []
    speaker_labels = {}
    # Token whisper memakai garis waktu tanpa hening saat --vad; tabel ini mengembalikannya ke waktu asli.
    vad_map = parse_vad_map(completed.stderr) if turns is not None else []
    for segment in payload.get("transcription", []):
        text = segment.get("text", "").strip()
        offsets = segment.get("offsets", {})
        if not text:
            continue
        start, end = round(offsets.get("from", 0) / 1000, 2), round(offsets.get("to", 0) / 1000, 2)
        if turns is None:
            transcript_segments.append({"start": start, "end": end, "text": text})
            continue
        # Satu kalimat whisper bisa berisi 2 orang ("...gitu ya?" "Iya betul"): pecah di titik ganti pembicara.
        parts = split_by_speaker(segment_words(segment, vad_map), turns) or [
            (start, end, text, dominant_speaker(turns, start, end))
        ]
        for i, (part_start, part_end, part_text, speaker) in enumerate(parts):
            transcript_segments.append({
                "start": start if i == 0 else round(max(start, min(part_start, end)), 2),
                "end": end if i == len(parts) - 1 else round(max(start, min(part_end, end)), 2),
                "text": part_text,
                "speaker": label_for(speaker, speaker_labels),
            })

    language = payload.get("result", {}).get("language", language_code or "")
    duration = max((seg["end"] for seg in transcript_segments), default=0)
    return transcript_segments, language, duration, language_checks
