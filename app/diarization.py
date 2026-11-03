"""Speaker diarization lokal dengan sherpa-onnx: model PyAnnote segmentation-3.0 + 3D-Speaker ERes2Net VoxCeleb (ONNX, CPU).

Tanpa PyTorch, token, atau login Hugging Face; model diunduh oleh app/bootstrap.py.
"""

import os
import re
import threading
import wave
from importlib.util import find_spec
from pathlib import Path

import numpy as np

from app.config import DIARIZATION_EMBEDDING_MODEL, DIARIZATION_SEGMENTATION_MODEL

CLUSTER_THRESHOLD = float(os.getenv("DIARIZATION_THRESHOLD", "1.1"))
_engine = None
_engine_speakers = 0
# Satu instance model dipakai bersama; proses diarization dijalankan bergantian.
_engine_lock = threading.Lock()


def diarization_available() -> bool:
    """Library sherpa-onnx dan kedua model sudah ada."""
    return (
        DIARIZATION_SEGMENTATION_MODEL.is_file()
        and DIARIZATION_EMBEDDING_MODEL.is_file()
        and find_spec("sherpa_onnx") is not None
    )


MAX_SPEAKERS = 20


def _config(num_speakers: int):
    import sherpa_onnx

    threads = max(1, min(8, os.cpu_count() or 4))
    segmentation = sherpa_onnx.OfflineSpeakerSegmentationModelConfig()
    segmentation.pyannote.model = str(DIARIZATION_SEGMENTATION_MODEL)
    segmentation.num_threads = threads
    embedding = sherpa_onnx.SpeakerEmbeddingExtractorConfig()
    embedding.model = str(DIARIZATION_EMBEDDING_MODEL)
    embedding.num_threads = threads
    config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=segmentation,
        embedding=embedding,
        # num_speakers 0 = ditebak dari kemiripan suara (num_clusters=-1 + threshold); lebih kecil = lebih banyak orang.
        # Model + 1.1 dipilih dari benchmark 8 model pada 6 percakapan uji LibriSpeech (2-5 orang, giliran cepat):
        # jumlah orang tertebak hampir tepat; 1.2 sudah menggabungkan orang berbeda, 1.0 memecah satu orang jadi dua.
        clustering=sherpa_onnx.FastClusteringConfig(
            num_clusters=num_speakers if num_speakers > 0 else -1, threshold=CLUSTER_THRESHOLD
        ),
        min_duration_on=0.3,
        min_duration_off=0.5,
    )
    if not config.validate():
        raise RuntimeError("Konfigurasi diarization tidak valid. Jalankan ulang: python -m app.bootstrap")
    return config


def speaker_turns(wav_path: Path, num_speakers: int = 0) -> list[tuple[float, float, int]]:
    """Giliran bicara (mulai, selesai, nomor pembicara). wav_path = WAV 16 kHz mono 16-bit dari convert_to_wav.

    num_speakers: 0 = otomatis, atau jumlah pembicara yang sudah diketahui (1..MAX_SPEAKERS).
    """
    global _engine, _engine_speakers
    with wave.open(str(wav_path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise RuntimeError("Diarization butuh WAV mono 16-bit.")
        rate = wav.getframerate()
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float32) / 32768.0

    with _engine_lock:
        if _engine is None:
            import sherpa_onnx

            _engine = sherpa_onnx.OfflineSpeakerDiarization(_config(num_speakers))
        elif _engine_speakers != num_speakers:
            _engine.set_config(_config(num_speakers))
        _engine_speakers = num_speakers
        if rate != _engine.sample_rate:
            raise RuntimeError(f"Diarization butuh audio {_engine.sample_rate} Hz, didapat {rate} Hz.")
        result = _engine.process(samples).sort_by_start_time()
    turns = [(seg.start, seg.end, seg.speaker) for seg in result]
    return absorb_minor_speakers(turns) if num_speakers == 0 else turns


Turn = tuple[float, float, int]  # (mulai, selesai, nomor pembicara mentah)

# Mode Otomatis: "pembicara" dengan total bicara < 2% dianggap pecahan (gema, bising, saling potong) dan digabung.
# Diskusi uji 56 menit: tanpa ini 27 pembicara (21 di antaranya < 40 detik); dengan ini 6.
MIN_SPEAKER_SHARE = float(os.getenv("DIARIZATION_MIN_SHARE", "0.02"))


def absorb_minor_speakers(turns: list[Turn], min_share: float = MIN_SPEAKER_SHARE) -> list[Turn]:
    """Giliran milik pembicara kecil diberikan ke pembicara utama yang paling dekat waktunya."""
    total = sum(end - start for start, end, _ in turns)
    talk: dict[int, float] = {}
    for start, end, speaker in turns:
        talk[speaker] = talk.get(speaker, 0.0) + end - start
    major = {spk for spk, t in talk.items() if t >= min_share * total}
    if not major or len(major) == len(talk):
        return turns
    anchors = [(start, end, spk) for start, end, spk in turns if spk in major]

    def nearest(start: float, end: float) -> int:
        return min(anchors, key=lambda a: max(a[0] - end, start - a[1], 0.0))[2]

    return [(start, end, spk if spk in major else nearest(start, end)) for start, end, spk in turns]

VAD_MAP_RE = re.compile(r"orig_start: ([\d.]+), orig_end: ([\d.]+), vad_start: ([\d.]+), vad_end: ([\d.]+)")
# Potongan pembicara lebih pendek dari ini dianggap noise dan digabung ke potongan sebelumnya.
MIN_PART_SECONDS = 0.25


def dominant_speaker(turns: list[Turn], start: float, end: float) -> int | None:
    """Nomor pembicara mentah dengan overlap waktu terbesar di [start, end]; None jika tidak ada."""
    best_speaker, best_overlap = None, 0.0
    for turn_start, turn_end, speaker in turns:
        if turn_start >= end:
            break  # turns urut waktu mulai
        overlap = min(end, turn_end) - max(start, turn_start)
        if overlap > best_overlap:
            best_speaker, best_overlap = speaker, overlap
    return best_speaker


def label_for(speaker: int | None, labels: dict[int, str]) -> str:
    """Nomor urut sesuai kemunculan pertama: Pembicara 1, 2, ..."""
    if speaker is None:
        return "Unknown"
    if speaker not in labels:
        labels[speaker] = f"Pembicara {len(labels) + 1}"
    return labels[speaker]


def speaker_for_segment(turns: list[Turn], start: float, end: float, labels: dict[int, str]) -> str:
    """Label pembicara yang paling lama bicara di rentang [start, end]."""
    return label_for(dominant_speaker(turns, start, end), labels)


def merge_fragments(items: list[dict], max_words: int = 2, max_gap: float = 0.3) -> list[dict]:
    """Gabungkan baris sangat pendek (<= max_words kata) ke baris sebelumnya bila pembicaranya sama dan jaraknya dekat.

    Batas kalimat whisper kadang menyisakan 1 kata ("In", "It") sebagai baris sendiri; ini hanya merapikan tampilan.
    """
    merged: list[dict] = []
    for item in items:
        prev = merged[-1] if merged else None
        if (
            prev is not None
            and prev.get("speaker") == item.get("speaker")
            and item["start"] - prev["end"] <= max_gap
            and len(item["text"].split()) <= max_words
        ):
            prev["text"] = f'{prev["text"]} {item["text"]}'
            prev["end"] = item["end"]
        else:
            merged.append(dict(item))
    return merged


def parse_vad_map(whisper_log: str) -> list[tuple[float, float, float, float]]:
    """Tabel (orig_start, orig_end, vad_start, vad_end) dari log whisper-cli --vad, dalam detik."""
    return [tuple(map(float, m)) for m in VAD_MAP_RE.findall(whisper_log)]


def to_original_time(t: float, vad_map: list[tuple[float, float, float, float]]) -> float:
    """Waktu token whisper (garis waktu tanpa hening) -> waktu asli audio. Tanpa VAD: tidak berubah."""
    for orig_start, orig_end, vad_start, vad_end in vad_map:
        if t <= vad_end:
            return min(orig_end, orig_start + max(0.0, t - vad_start))
    if vad_map:
        orig_end, vad_end = vad_map[-1][1], vad_map[-1][3]
        return orig_end + (t - vad_end)
    return t


def segment_words(segment: dict, vad_map) -> list[tuple[float, float, str]]:
    """Token whisper -> kata utuh (mulai, selesai, teks) di waktu asli. Token baru tanpa spasi depan = lanjutan kata."""
    words: list[list] = []
    for token in segment.get("tokens", []):
        text = token.get("text", "")
        if not text or text.startswith("[_") or text.startswith("<|"):
            continue  # token khusus whisper seperti [_BEG_], [_TT_123]
        start = to_original_time(token["offsets"]["from"] / 1000, vad_map)
        end = to_original_time(token["offsets"]["to"] / 1000, vad_map)
        if words and not text.startswith(" "):
            words[-1][1] = max(words[-1][1], end)
            words[-1][2] += text
        else:
            words.append([start, end, text])
    return [(a, b, t) for a, b, t in words]


def split_by_speaker(words: list[tuple[float, float, str]], turns: list[Turn]) -> list[tuple[float, float, str, int | None]]:
    """Kelompokkan kata berurutan per pembicara: (mulai, selesai, teks, pembicara mentah)."""
    parts: list[list] = []
    for start, end, text in words:
        speaker = dominant_speaker(turns, start, max(end, start + 0.01))
        if parts and (speaker is None or speaker == parts[-1][3]):
            parts[-1][1], parts[-1][2] = end, parts[-1][2] + text
        else:
            parts.append([start, end, text, speaker])
    merged: list[list] = []
    for part in parts:
        too_short = part[1] - part[0] < MIN_PART_SECONDS or not any(c.isalnum() for c in part[2])
        if merged and (too_short or part[3] == merged[-1][3]):
            merged[-1][1], merged[-1][2] = part[1], merged[-1][2] + part[2]
        else:
            merged.append(part)
    if len(merged) > 1 and merged[0][3] is None:  # awal kalimat tanpa pembicara -> ikut potongan berikutnya
        merged[1][0], merged[1][2] = merged[0][0], merged[0][2] + merged[1][2]
        merged.pop(0)
    return [(a, b, t.strip(), spk) for a, b, t, spk in merged if t.strip()]
