import os
from importlib.util import find_spec

diarization_pipeline = None
diarization_error = None


def diarization_available() -> bool:
    """Checks if PyAnnote diarization dependencies and token are ready."""
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    return bool(token and find_spec("pyannote.audio"))


def load_diarization_pipeline():
    """Loads the speaker diarization pipeline on demand."""
    global diarization_pipeline, diarization_error

    if diarization_pipeline is not None:
        return diarization_pipeline

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        diarization_error = "HF_TOKEN belum diatur. PyAnnote membutuhkan token Hugging Face."
        return None

    try:
        from pyannote.audio import Pipeline

        try:
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=token,
            )
        except TypeError:
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=token,
            )
        diarization_error = None
        return diarization_pipeline
    except Exception as exc:
        diarization_error = str(exc)
        return None


def speaker_for_segment(diarization, start: float, end: float, labels: dict[str, str]) -> str:
    """Matches a Whisper transcription segment to the most overlapping diarized speaker."""
    best_speaker = "Unknown"
    best_overlap = 0.0
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        overlap = max(0.0, min(end, turn.end) - max(start, turn.start))
        if overlap > best_overlap:
            best_overlap = overlap
            if speaker not in labels:
                labels[speaker] = f"Pembicara {len(labels) + 1}"
            best_speaker = labels[speaker]
    return best_speaker
