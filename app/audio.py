import wave
from pathlib import Path


def _resampled_frame_bytes(frame) -> bytes:
    samples = frame.to_ndarray().reshape(-1)
    if samples.dtype.byteorder == ">":
        samples = samples.byteswap()
    return samples.astype("<i2", copy=False).tobytes()


def convert_to_wav(source_path: Path, target_path: Path) -> None:
    """
    Converts any audio or video container to 16kHz mono 16-bit PCM WAV.
    The file is written with Python's wave module so whisper.cpp gets a plain
    RIFF/PCM header.
    """
    import av

    has_frames = False
    with av.open(str(source_path), mode="r", metadata_errors="ignore") as in_container:
        audio_streams = [s for s in in_container.streams if s.type == "audio"]
        if not audio_streams:
            raise RuntimeError("File tidak memiliki audio stream.")

        audio_stream = audio_streams[0]
        resampler = av.audio.resampler.AudioResampler(
            format="s16",
            layout="mono",
            rate=16000,
        )

        with wave.open(str(target_path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            for frame in in_container.decode(audio_stream):
                for resampled in resampler.resample(frame):
                    has_frames = True
                    output.writeframes(_resampled_frame_bytes(resampled))

            for resampled in resampler.resample(None):
                has_frames = True
                output.writeframes(_resampled_frame_bytes(resampled))

    if not has_frames:
        raise RuntimeError("Gagal mengonversi audio: stream kosong atau tidak ada audio frame yang terbaca.")


def extract_audio_track(source_path: Path, target_path: Path, sample_rate: int = 44100) -> None:
    """
    Extracts original quality audio track from a video/audio container
    to standard WAV (44.1kHz 16-bit PCM stereo/mono).
    """
    import av

    has_frames = False
    with av.open(str(source_path), mode="r", metadata_errors="ignore") as in_container:
        audio_streams = [s for s in in_container.streams if s.type == "audio"]
        if not audio_streams:
            raise RuntimeError("File tidak memiliki jalur audio.")

        audio_stream = audio_streams[0]
        channels = audio_stream.codec_context.channels or 1
        layout = "stereo" if channels >= 2 else "mono"

        resampler = av.audio.resampler.AudioResampler(
            format="s16",
            layout=layout,
            rate=sample_rate,
        )

        output_channels = 2 if layout == "stereo" else 1
        with wave.open(str(target_path), "wb") as output:
            output.setnchannels(output_channels)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            for frame in in_container.decode(audio_stream):
                for resampled in resampler.resample(frame):
                    has_frames = True
                    output.writeframes(_resampled_frame_bytes(resampled))

            for resampled in resampler.resample(None):
                has_frames = True
                output.writeframes(_resampled_frame_bytes(resampled))

    if not has_frames:
        raise RuntimeError("Tidak ada audio yang berhasil diekstrak dari file ini.")
