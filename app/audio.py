import wave
from array import array
from pathlib import Path


def convert_to_wav(source_path: Path, target_path: Path) -> None:
    """Converts any audio or video container to 16kHz mono WAV for Whisper."""
    import av

    resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)
    pcm = array("h")
    with av.open(str(source_path), mode="r", metadata_errors="ignore") as container:
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                pcm.extend(resampled.to_ndarray().reshape(-1).tolist())

    with wave.open(str(target_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(pcm.tobytes())


def extract_audio_track(source_path: Path, target_path: Path, sample_rate: int = 44100) -> None:
    """Extracts original quality audio track from a video/audio container."""
    import av

    with av.open(str(source_path), mode="r", metadata_errors="ignore") as container:
        if not container.streams.audio:
            raise RuntimeError("File tidak memiliki jalur audio.")
        channels = container.streams.audio[0].codec_context.channels or 1
        layout = "stereo" if channels >= 2 else "mono"
        resampler = av.audio.resampler.AudioResampler(format="s16", layout=layout, rate=sample_rate)
        pcm = array("h")
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                pcm.extend(resampled.to_ndarray().reshape(-1).tolist())

    if not pcm:
        raise RuntimeError("Tidak ada audio yang berhasil diekstrak dari file ini.")

    with wave.open(str(target_path), "wb") as output:
        output.setnchannels(2 if layout == "stereo" else 1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm.tobytes())
