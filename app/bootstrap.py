"""Menyiapkan semua file besar yang tidak ada di git: dependensi Python, whisper-cli, dan model.

Aman dijalankan berulang: yang sudah ada dilewati. Dipanggil otomatis oleh scripts/start_app.sh / .bat.
Manual: python -m app.bootstrap   (hanya pakai library standar, jadi bisa jalan sebelum .venv ada)
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
IS_WINDOWS = os.name == "nt"
MODELS_DIR = BASE_DIR / "models"

# (nama file, URL, sha256) — checksum sama dengan yang dipublikasikan Hugging Face.
MODELS = [
    (
        "ggml-large-v3-turbo-q5_0.bin",
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin",
        "394221709cd5ad1f40c46e6031ca61bce88931e6e088c188294c6d5a55ffa7e2",
    ),
    (
        "ggml-silero-v5.1.2.bin",
        "https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v5.1.2.bin",
        "29940d98d42b91fbd05ce489f3ecf7c72f0a42f027e4875919a28fb4c04ea2cf",
    ),
]

# Speaker diarization (sherpa-onnx, tanpa login Hugging Face): (nama file, URL, sha256 unduhan, file di dalam arsip).
SHERPA_MODELS = "https://github.com/k2-fsa/sherpa-onnx/releases/download"
DIARIZATION_MODELS = [
    (
        "pyannote-segmentation-3.0.onnx",
        f"{SHERPA_MODELS}/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2",
        "24615ee884c897d9d2ba09bb4d30da6bb1b15e685065962db5b02e76e4996488",
        "sherpa-onnx-pyannote-segmentation-3-0/model.onnx",
    ),
    (
        "3dspeaker_speech_eres2net_sv_en_voxceleb_16k.onnx",
        f"{SHERPA_MODELS}/speaker-recongition-models/3dspeaker_speech_eres2net_sv_en_voxceleb_16k.onnx",
        "c59158379255ad66e161679cca6af8d52d51e389e3224ab7d7a7baae295c2db5",
        None,
    ),
]

# Linux: whisper.cpp di-build dari source pada commit ini (versi yang sudah dites dengan aplikasi).
WHISPER_REPO = "https://github.com/lemonade-sdk/whisper.cpp-amd.git"
WHISPER_COMMIT = "bd9985cf0b1ad53889ed90a71eac6830ebd341ae"
WHISPER_SOURCE = BASE_DIR / "third_party" / "whisper.cpp-amd"

# Windows: build Vulkan siap pakai (whisper-cli.exe + DLL, MIT) dari GitHub Release project ini.
# Build sendiri di Windows butuh Visual Studio + Vulkan SDK, jadi diunduh saja.
# Runtime Visual C++ sengaja tidak ikut di zip (lisensi Microsoft); pengguna menginstallnya dari Microsoft.
WINDOWS_BINARY_URL = os.getenv(
    "WHISPER_WINDOWS_URL",
    "https://github.com/theCrudify/01.-Audio-Transcrypt/releases/download/whisper-vulkan-bd9985c/whisper-vulkan-windows-x64.zip",
)
WINDOWS_BINARY_SHA256 = os.getenv(
    "WHISPER_WINDOWS_SHA256", "3da7193b83ef5ea0c6c419ec77cfffc40ddaa2cb13e6c551fab6752e4408ce1b"
)
WINDOWS_CLI_DIR = BASE_DIR / "build-vulkan" / "bin" / "Release"
# Cadangan jika rilis Vulkan di atas belum ada: build CPU resmi dari ggml-org (tidak disebarkan ulang oleh project ini).
OFFICIAL_CPU_URL = "https://github.com/ggml-org/whisper.cpp/releases/download/b5454/whisper-bin-x64.zip"
OFFICIAL_CPU_SHA256 = "6ba69e3482d7826214f90a6a9c84ca07782aec1e1d0c6a7c30c994fd5d816ccb"
VC_REDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
VC_RUNTIME_DLLS = ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "vcomp140.dll")
LINUX_CLI = BASE_DIR / "build-linux" / "bin" / "whisper-cli"

VENV_DIR = BASE_DIR / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
REQUIREMENTS = BASE_DIR / "requirements" / "base.txt"


class SetupError(Exception):
    """Langkah setup gagal; pesannya sudah berisi cara memperbaikinya."""


def log(message: str) -> None:
    print(f"[setup] {message}", flush=True)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, target: Path, expected_sha256: str) -> None:
    """Unduh ke file .part, cek sha256, baru pindahkan; unduhan yang terputus tidak meninggalkan file rusak."""
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    log(f"Mengunduh {target.name} ...")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "AudioTranscrypt-setup"})
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            done, last_step = 0, -1
            while block := response.read(1024 * 1024):
                out.write(block)
                done += len(block)
                # Refresh every 5% so logs stay short when output is not a terminal.
                if total and (step := done * 20 // total) != last_step:
                    print(f"\r        {done * 100 // total:3d}%  {done / 1e6:,.0f} / {total / 1e6:,.0f} MB", end="", flush=True)
                    last_step = step
        print(flush=True)
    except OSError as exc:
        partial.unlink(missing_ok=True)
        raise SetupError(f"Gagal mengunduh {url}\n        {exc}\n        Cek koneksi internet lalu jalankan ulang.") from exc

    actual = sha256_of(partial)
    if actual != expected_sha256:
        partial.unlink(missing_ok=True)
        raise SetupError(f"Checksum {target.name} tidak cocok (unduhan rusak atau file berubah). Jalankan ulang.")
    partial.replace(target)


def license_path(model: Path) -> Path:
    """Teks lisensi yang ikut arsip model, disimpan di samping modelnya (lisensi MIT mewajibkan ini disertakan)."""
    return model.with_name(model.name.rsplit(".", 1)[0] + ".LICENSE.txt")


def download_from_archive(url: str, target: Path, expected_sha256: str, member: str) -> None:
    """Unduh arsip .tar.bz2 (dicek sha256), ambil model + file LICENSE-nya, lalu hapus arsipnya."""
    archive = target.with_name(target.name + ".tar.bz2")
    download(url, archive, expected_sha256)
    partial = target.with_name(target.name + ".part")
    try:
        with tarfile.open(archive, "r:bz2") as bundle:
            source = bundle.extractfile(member)
            if source is None:
                raise SetupError(f"{member} tidak ada di dalam {archive.name}.")
            with source, partial.open("wb") as out:
                shutil.copyfileobj(source, out)
            license_member = member.rsplit("/", 1)[0] + "/LICENSE"
            if license_member in bundle.getnames():
                license_source = bundle.extractfile(license_member)
                if license_source is not None:
                    with license_source:
                        license_path(target).write_bytes(license_source.read())
        partial.replace(target)
    except (OSError, tarfile.TarError, KeyError) as exc:
        partial.unlink(missing_ok=True)
        raise SetupError(f"Gagal mengekstrak {archive.name}: {exc}") from exc
    finally:
        archive.unlink(missing_ok=True)


def ensure_models() -> None:
    if not os.getenv("WHISPER_MODEL_PATH"):  # model whisper ditentukan sendiri oleh pengguna
        for name, url, sha in MODELS:
            if not (MODELS_DIR / name).is_file():
                download(url, MODELS_DIR / name, sha)
    for name, url, sha, member in DIARIZATION_MODELS:
        target = MODELS_DIR / name
        if target.is_file() and (not member or license_path(target).is_file()):
            continue
        if member:
            download_from_archive(url, target, sha, member)
        else:
            download(url, target, sha)


def missing_vc_runtime(system_dir: Path, app_dir: Path) -> list[str]:
    """DLL runtime Visual C++ yang dibutuhkan whisper-cli.exe tapi tidak ada di System32 maupun folder whisper."""
    return [name for name in VC_RUNTIME_DLLS if not (system_dir / name).is_file() and not (app_dir / name).is_file()]


def ensure_vc_runtime() -> None:
    """Jika runtime Visual C++ belum ada, unduh installer resminya dari Microsoft lalu jalankan (muncul prompt admin)."""
    system_dir = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    if not missing_vc_runtime(system_dir, WINDOWS_CLI_DIR):
        return
    manual = f"Install manual dari {VC_REDIST_URL}, lalu jalankan ulang script ini."
    installer = BASE_DIR / "build-vulkan" / "vc_redist.x64.exe"
    installer.parent.mkdir(parents=True, exist_ok=True)
    log("Microsoft Visual C++ Redistributable belum terpasang. Mengunduh installer resmi dari Microsoft ...")
    try:
        # shortcut: no sha256 pin because Microsoft updates this file in place; trust rests on HTTPS to microsoft.com.
        request = urllib.request.Request(VC_REDIST_URL, headers={"User-Agent": "AudioTranscrypt-setup"})
        with urllib.request.urlopen(request, timeout=60) as response, installer.open("wb") as out:
            shutil.copyfileobj(response, out)
    except OSError as exc:
        installer.unlink(missing_ok=True)
        raise SetupError(f"Gagal mengunduh installer Visual C++: {exc}\n        {manual}") from exc
    log("Menginstall Visual C++ Redistributable (setujui prompt administrator yang muncul) ...")
    try:
        code = subprocess.run([str(installer), "/install", "/passive", "/norestart"]).returncode
    except OSError as exc:
        raise SetupError(f"Installer Visual C++ gagal dijalankan: {exc}\n        {manual}") from exc
    finally:
        installer.unlink(missing_ok=True)
    # 0 = ok, 3010 = ok tapi perlu restart, 1638 = versi lebih baru sudah ada.
    if code not in (0, 3010, 1638) or missing_vc_runtime(system_dir, WINDOWS_CLI_DIR):
        raise SetupError(f"Install Visual C++ Redistributable belum berhasil (kode {code}).\n        {manual}")


def extract_cli(archive: Path, target_dir: Path) -> None:
    """Ambil whisper-cli.exe + DLL-nya dari zip (zip resmi menaruhnya di folder Release/), buang sisanya."""
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.namelist():
            name = member.rsplit("/", 1)[-1]
            if name == "whisper-cli.exe" or name.endswith(".dll") or name.startswith("LICENSE"):
                (target_dir / name).write_bytes(bundle.read(member))
    archive.unlink()


def ensure_windows_cli() -> None:
    ensure_vc_runtime()
    cpu_marker = WINDOWS_CLI_DIR / "CPU_ONLY.txt"
    has_cli = (WINDOWS_CLI_DIR / "whisper-cli.exe").is_file()
    if has_cli and not cpu_marker.is_file():
        return
    archive = BASE_DIR / "build-vulkan" / "whisper-vulkan-windows-x64.zip"
    try:
        download(WINDOWS_BINARY_URL, archive, WINDOWS_BINARY_SHA256)
    except SetupError:
        if has_cli:
            return  # tetap pakai build CPU; dicoba lagi di run berikutnya
        log("Build Vulkan (GPU) belum tersedia. Memakai whisper.cpp resmi versi CPU (lebih lambat) ...")
        archive = BASE_DIR / "build-vulkan" / "whisper-bin-x64.zip"
        download(OFFICIAL_CPU_URL, archive, OFFICIAL_CPU_SHA256)
        extract_cli(archive, WINDOWS_CLI_DIR)
        cpu_marker.write_text("whisper.cpp resmi versi CPU; diganti build Vulkan otomatis saat tersedia.\n")
        log("whisper-cli Windows (CPU) siap.")
        return
    if WINDOWS_CLI_DIR.is_dir():
        shutil.rmtree(WINDOWS_CLI_DIR)  # buang DLL build CPU agar tidak tercampur
    extract_cli(archive, WINDOWS_CLI_DIR)
    log("whisper-cli Windows (Vulkan GPU) siap.")


def ensure_linux_cli() -> None:
    if LINUX_CLI.is_file():
        return
    missing = [tool for tool in ("git", "cmake", "c++", "glslc") if not shutil.which(tool)]
    if missing:
        raise SetupError(
            "whisper-cli belum ada dan perlu di-build, tapi tool berikut belum terpasang: "
            + ", ".join(missing)
            + "\n        Debian/Ubuntu: sudo apt install git build-essential cmake libvulkan-dev glslc mesa-vulkan-drivers"
        )
    if not (WHISPER_SOURCE / "CMakeLists.txt").is_file():
        log("Mengambil source whisper.cpp ...")
        WHISPER_SOURCE.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--quiet", WHISPER_REPO, str(WHISPER_SOURCE)])
        run(["git", "-C", str(WHISPER_SOURCE), "checkout", "--quiet", WHISPER_COMMIT])
    log("Build whisper.cpp dengan Vulkan (sekali saja, beberapa menit) ...")
    run(["bash", str(BASE_DIR / "scripts" / "build_whisper.sh")])
    if not LINUX_CLI.is_file():
        raise SetupError(f"Build selesai tapi {LINUX_CLI} tidak ditemukan. Cek output build di atas.")


def ensure_whisper_cli() -> None:
    if os.getenv("WHISPER_CLI"):
        return  # binary ditentukan sendiri oleh pengguna
    if IS_WINDOWS:
        ensure_windows_cli()
    else:
        ensure_linux_cli()


def ensure_venv() -> None:
    """Buat .venv dan install requirements; install ulang hanya jika requirements/base.txt berubah."""
    marker = VENV_DIR / ".requirements.sha256"
    wanted = sha256_of(REQUIREMENTS)
    if VENV_PYTHON.is_file() and marker.is_file() and marker.read_text().strip() == wanted:
        return
    if not VENV_PYTHON.is_file():
        log("Membuat virtual environment .venv ...")
        try:
            run([sys.executable, "-m", "venv", str(VENV_DIR)])
        except SetupError as exc:
            hint = "" if IS_WINDOWS else "\n        Debian/Ubuntu: sudo apt install python3-venv"
            raise SetupError(f"{exc}{hint}") from exc
    log("Menginstall dependensi Python ...")
    run([str(VENV_PYTHON), "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", str(REQUIREMENTS)])
    marker.write_text(wanted)


def run(command: list[str]) -> None:
    try:
        subprocess.run(command, cwd=BASE_DIR, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SetupError(f"Perintah gagal: {' '.join(command)}\n        {exc}") from exc


def main() -> int:
    if sys.version_info < (3, 10):
        log(f"Butuh Python 3.10+, yang terpasang {sys.version.split()[0]}.")
        return 1
    try:
        ensure_venv()
        ensure_whisper_cli()
        ensure_models()
    except SetupError as exc:
        log(f"GAGAL: {exc}")
        return 1
    log("Semua file siap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
